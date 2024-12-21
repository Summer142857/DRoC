from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from common import *
from utils import context_or_tools_codes, context_gurobi_codes, write_code_to_file, merge_retriever
from langchain_core.prompts import PromptTemplate
from langchain.globals import set_debug
import warnings
from langchain.tools.retriever import create_retriever_tool
from langchain_anthropic import ChatAnthropic

set_debug(False)

def decomposer(problem, llm="gpt-4o"):
    # LLM with function call
    if llm.startswith("llama"):
        llm = ChatOllama(
            model=llm,
            temperature=0,
        )
    elif llm.startswith("gpt"):
        llm = ChatOpenAI(model=llm, temperature=0.0, verbose=True)
    elif llm.startswith("claude"):
        llm = ChatAnthropic(model=llm, temperature=0.0, max_tokens=5000)
    else:
        raise NotImplementedError("llm not supported!")

    # Prompt
    system = """You will extract the keywords of a vehicle routing problem (VRP) for me. \n
    I give you the name of a VRP and you produce the keywords according to its constraints.\n
    Structure your answer with a list of keywords inside "<>" and use commas to separate different keywords. Do not return other things. \n
    For example, the output of "Capacitated Vehicle Routing Problem with Time Windows and Multiple Depots (CVRPTWMD)" should be <Capacitated, Time Windows, Multiple Depots>, \n
    and the output of "Prize Collecting Travelling Salesman Problem (PCTSP)" should be <Prize Collecting>."""
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            ("human", "Here is the name of the VRP: \n\n {problem}"),
        ]
    )
    keyword_extractor = prompt | llm
    res = keyword_extractor.invoke({"problem": problem}).content.replace("<", "").replace(">", "").split(",")
    return res


def summarize_document(solver, keyword, context, llm="gpt-4o"):
    if llm.startswith("llama"):
        llm = ChatOllama(
            model=llm,
            temperature=0,
        )
    elif llm.startswith("gpt"):
        llm = ChatOpenAI(model=llm, temperature=0.0, verbose=True)
    elif llm.startswith("claude"):
        llm = ChatAnthropic(model=llm, temperature=0.0, max_tokens=5000)
    else:
        raise NotImplementedError("llm not supported!")

    # Data model
    class summary(BaseModel):
        """Summary for retrieved document."""
        relevance: str = Field(description="Relevance score 'yes' or 'no'")
        code_snippet: str = Field(description="key code snippet to program a specific constraint")
        summary: str = Field(description="textual summary on how to correctly program a specific constraint")

    model = llm.with_structured_output(summary)

    # Prompt
    prompt = PromptTemplate(
        template="""You are an expert in Python programming and {solver} for vehicle routing problem. \n
        I will give you a retrieved documents potentially related to {keyword}, and you will firstly assess if the document includes Python code to program {keyword}. \n
        If so, you should explain how the code address the constraint of {keyword}. \n
        Here is the retrieved document: \n\n {context} \n\n
        If the document contains Python code related to {keyword}, grade it as relevant. \n
        After that, extract the code snippet in the document related to {keyword}. \n
        Finally, produce an explanation on how to program the constraint of {keyword}, and your goal is to make other programmers know how to do that. \n
        Structure your answer with the binary score 'yes' or 'no' to indicate whether the document is relevant, and then list the related code snippet, and finally give the summary. \n
        If the document is not related, just return 'no' for the binary score, and nothing for the code snippet and the summary.""",
        input_variables=["solver", "context", "keyword"],
    )

    # Chain
    chain = prompt | model

    result = chain.invoke({"solver": solver, "context": context, "keyword": keyword})

    return result


def branched_retriever(problem, solver="or-tools", llm="gpt-4o"):
    """Retrieve from example codes based on the constraint keywords of the problem."""
    llm_call = 0
    prompt = PromptTemplate(
        template="""You are an expert in Python programming and {solver} for vehicle routing problem (VRP).\n
        I will give you several retrieved documents (codes) and their explanations potentially related to {keyword}, and you should assess which context is the most relevant one and with minimal redundant information.\n
        Here are the documents, which are seperated by '====================': \n
        {contexts} \n
        Return the index of the most relevant document and do not return anything else. For example, if you think the second document is the most relevant one, just return 2.
        Please strictly return integer index following the above instruction.
        """,
        input_variables=["solver", "contexts", "keyword"],
    )
    if llm.startswith("gpt"):
        llm = ChatOpenAI(model=llm, temperature=0.0, verbose=True)
    elif llm.startswith("claude"):
        llm = ChatAnthropic(model=llm, temperature=0.0, max_tokens=5000)
    else:
        raise NotImplementedError
    chain = prompt | llm

    keywords = decomposer(problem)
    if solver == "OR-tools":
        retriever = context_or_tools_codes()
        # retriever = merge_retriever()
    elif solver == "Gurobi":
        retriever = context_gurobi_codes()
    else:
        raise NotImplementedError
    keyword_context = {}
    keyword_summary = {}
    for keyword in keywords:
        docs = retriever.invoke("Python code of " + keyword)
        contexts = []
        summaries = []
        contexts_input = []
        for doc in docs:
            summary_context = summarize_document(solver, keyword, doc)
            llm_call += 1
            if summary_context.relevance == "yes":
                contexts.append(doc)
                summaries.append(summary_context.code_snippet + '\n' + summary_context.summary)
                contexts_input.append(doc.page_content + '\n' + summary_context.summary)
        contexts = [c.page_content for c in contexts]
        if len(contexts) > 1:
            filter_context = " \n ====== \n ".join(contexts_input)
            idx = chain.invoke({"solver": solver, "contexts": filter_context, "keyword": keyword}).content
            llm_call += 1
            try:
                idx = int(idx) - 1
            except:
                idx = 0
                warnings.warn("the return value of the filter process is not correct!", RuntimeWarning)
        else:
            idx = 0
        if len(contexts) != 0:
            keyword_context[keyword] = contexts[idx]
            keyword_summary[keyword] = summaries[idx]
    print("============Context filter successful! LLM call " + str(llm_call) + " times============")
    return keyword_context, keyword_summary


def self_debug(state: code, input: dict, llm="gpt-4o"):
    """Call to fix the error of the code based on an LLM when there are syntax error, incomplete program, or other errors."""

    if llm.startswith("gpt"):
        model = ChatOpenAI(model=llm, temperature=0.0, verbose=True)
    elif llm.startswith("claude"):
        model = ChatAnthropic(model=llm, temperature=0.0, max_tokens=5000)
    else:
        raise NotImplementedError

    prompt_template_debugger = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an expert in Python programming for operations research by calling {solver}. Now your responsibility is to debug the code snippet with errors."""
            ),
            ("user",
             """
The code snippet with bug is as <{prep_code}>. Here is the error message of the code: <{message}>.
You can first reason about the error, and finally refine the code and return the whole fixed function.
Ensure any code you provide can be executed with all required imports and variables defined.
Remember, the final solution should be returned by the 'solve' function. Do not use other name for the function and do not give example usage of the function.
Structure the refined solution by firstly giving the reason of the error and the strategy for fixing it.
Then list the imports. Finally list the functioning code block and solve the problem with 'solve' function.
"""
             )
        ]
    )
    chain = prompt_template_debugger | model.with_structured_output(code)
    res = chain.invoke(
        {'solver': input['solver'], 'prep_code': state['generation'].imports + "\n" + state['generation'].code,
         'message': state['messages']})
    return res


def retrieval_augmented_generate(input: dict, context: dict, llm="gpt-4o"):
    """Call to generate a new program for solving the problem, drawing upon the retrieved code in the context."""
    prompt_template_gen = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an expert in Python programming for operations research and combinatorial optimization. You are good at calling {solver} in Python and solve problems."""
            ),
            ("user",
             """
             Respond with the syntactically correct code for solving a {problem} using {solver}. Make sure you follow these rules:
            1. Read the template. First understand the meaning of the parameters in 'solve' function, and then complete the code inside the function.
            2. The context provides example codes of addressing each constraint of {problem} by {solver}. Learn to model each constraint and solve the problem accordingly.
            3. Do not give additional examples or define main function for testing.
            4. Return the objective value of the problem by the 'solve' function.
            5. Ensure any code you provide can be executed with all required imports and variables defined.

            Template:
            {code_example}

            Context:
            {context}

            Structure your answer with a description of the code solution, and then list the imports, and finally list the functioning code block.
                     """
             ),
            ("placeholder", "{messages}")
        ]
    )
    if llm.startswith("gpt"):
        model = ChatOpenAI(model=llm, temperature=0.0, verbose=True)
    elif llm.startswith("claude"):
        model = ChatAnthropic(model=llm, temperature=0.0, max_tokens=5000)
    else:
        raise NotImplementedError
    chain = prompt_template_gen | model.with_structured_output(code)

    c = ""
    for keyword in context.keys():
        c += "Constraint: " + keyword + "\nExample code: " + context[keyword] + "===============\n"
    input['context'] = c

    return chain.invoke(input)


def retrieval_augmented_refine(input: dict, context: dict, state: code, llm="gpt-4o"):
    """Call to refine the current generated code, which is with error, drawing upon the retrieved code in the context."""
    prompt_template_ref = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are responsible for refining the code with errors, which tries to solve {problem} by calling {solver} in Python."""
            ),
            ("user",
             """
            The code snippet with the bug is as <{prep_code}>.\n
            Here is the error message of the code: <{message}>.\n
            Make sure you follow these rules:
            1. You can first reason about the error, and then refine the code and return the whole fixed function.
            2. The context provides examples of solving problems with different constraints, referring to the relevant parts and modifying the code accordingly: <{context}>.\n
            3. Do not give additional examples or define the main function for testing.
            4. Return the objective value of the problem by the 'solve' function.
            5. Ensure any code you provide can be executed with all required imports and variables defined.

            Structure your answer with a description of the code solution, then list the imports, and finally list the functioning code block.
                     """
             ),
            ("placeholder", "{messages}")
        ]
    )
    if llm.startswith("gpt"):
        model = ChatOpenAI(model=llm, temperature=0.0, verbose=True)
    elif llm.startswith("claude"):
        model = ChatAnthropic(model=llm, temperature=0.0, max_tokens=5000)
    else:
        raise NotImplementedError
    chain = prompt_template_ref | model.with_structured_output(code)

    input['prep_code'] = state['generation'].imports + "\n" + state['generation'].code
    input['message'] = state['messages']
    c = ""
    for keyword in context.keys():
        c += "Constraint: " + keyword + "\nExample code: " + context[keyword] + "===============\n"
    input['context'] = c

    return chain.invoke(input)


class System():
    def __init__(self, input, params, llm):
        self.input = input
        self.params = params
        self.llm = llm
        self.max_iteration = 4
        self.retrieval_flag = False
        ret = context_or_tools_codes() if input['solver'] == "OR-tools" else context_gurobi_codes()
        # ret = merge_retriever() if input['solver'] == "OR-tools" else context_gurobi_codes()
        self.retriever = create_retriever_tool(ret,
        "retrieve_example_code",
        "Search and return example Python code for solving similar vehicle routing problems. Use it when the error is caused by incorrect use of solver API.",
        )
        self.context = None
        self.optimum = input['optimum']

    def standard_generator(self):
        prompt_template_gen = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are an expert in Python programming for operations research. You are good at calling {solver} in Python and solving problems."""
                ),
                ("user",
                 """
             Respond with the syntactically correct code for solving a {problem} using {solver}. Make sure you follow these rules:
1. Read the template. First understand the meaning of the parameters in 'solve' function, and then follow the format of the template strictly to generate code.
2. Ensure all parameters in the template are used in the function.
3. Do not give additional examples or define main function for testing.
4. Return the objective value of the problem by the 'solve' function.
5. Ensure any code you provide can be executed with all required imports and variables defined.

Template:
{code_example}

Structure your answer with a description of the code solution, and then list the imports, and finally list the functioning code block.
"""
                 ),
                ("placeholder", "{messages}")
            ]
        )
        if self.llm.startswith("gpt"):
            llm = ChatOpenAI(model=self.llm, temperature=0.0, verbose=True)
        elif self.llm.startswith("claude"):
            llm = ChatAnthropic(model=self.llm,
                                temperature=0.0, max_tokens=8000)
        else:
            raise NotImplementedError
        chain = prompt_template_gen | llm.with_structured_output(code)
        result = chain.invoke(self.input)

        state = GraphState(error='', messages=[], generation=result, iterations=0)
        state = code_check(state, self.params, self.optimum)
        return state


    def agent(self, input, params_dict, state):

        prompt = PromptTemplate(
            template="""
        Your task is to determine how to refine the incorrect Python code, which is produced by another programmer. \n
        Here is the code:
        <prep_code>

        The code is about solving a {problem} based on {solver}, and there is the error information while running the code: \n

        Error message:
        <{message}>

        There are several tools that can be called, which can be one of the following: \n
        (1) retrieval_augmented_refine[input]: Retrieve code examples from a repository, and then refine the current program drawing upon the retrieved codes.
        Prioritize it when the error is caused by incorrect use of solver API. \n
        (2) self_debug[input]: Call a pretrained LLM like yourself.
        Prioritize it when you are confident in fixing the error yourself, e.g., when the error of the code is caused by syntax error or wrong import. \n
        Return "1" if you think you should use tool (1), otherwise return "2". Do not return other things or give explanations.
        """,
            input_variables=["problem", "solver", "message"])

        # Choose the LLM that will drive the agent
        if self.llm.startswith("gpt"):
            llm = ChatOpenAI(model=self.llm, temperature=0.0, verbose=True)
        elif self.llm.startswith("claude"):
            llm = ChatAnthropic(model=self.llm,
                                temperature=0.0, max_tokens=5000)
        else:
            raise NotImplementedError
        model = prompt | llm
        res = model.invoke({"problem": input['problem'], "solver": input['solver'], "message": state["messages"]}).content
        if res == "1":
            print("======Retrieval_augmented_refine======")
            res_new = retrieval_augmented_refine(input, self.context, state)
        elif res == "2":
            print("======SELF-DEBUG======")
            res_new = self_debug(state, input, self.llm)
        else:
            raise RuntimeWarning("LLM agent doesn't return the correct value!")
        state_new = GraphState(error='', messages=[], generation=res_new, iterations=0)
        state_new = code_check(state_new, self.params, self.optimum)
        return state_new


    def run(self):
        iter = 0
        no_run_time_error = False
        accu_solution = False
        state = self.standard_generator()
        print(state)
        if state['error'] == 'no':
            no_run_time_error = True
            accu_solution = True
            write_code_to_file(self.input['problem'], state['generation'].imports, state['generation'].code, self.llm)
            return no_run_time_error, accu_solution
        while iter < self.max_iteration:
            iter += 1
            if state['error'] != 'no':
                message = state['messages']
                if len(message[0]) > 1:
                    if ("The obj. is far from the optimum" in message[0][1]
                            or "You did not finish the function" in message[0][
                                1] or "You solution returns nothing or 0" in message[0][1]):
                        no_run_time_error = True
                if self.context is None:
                    # If fail, conduct RAG for the first round
                    self.context, summary = branched_retriever(self.input['problem'], self.input['solver'], self.llm)
                    print(self.context)
                    res = retrieval_augmented_generate(self.input, self.context, self.llm)
                    state = GraphState(error='', messages=[], generation=res, iterations=iter)
                    state = code_check(state, self.params, self.optimum)
                else:
                    # agentic operation
                    state = self.agent(self.input, self.params, state)
                print(state)
            else:
                no_run_time_error = True
                accu_solution = True
                write_code_to_file(self.input['problem'], state['generation'].imports, state['generation'].code, self.llm)
                return no_run_time_error, accu_solution
        return no_run_time_error, accu_solution