from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.globals import set_debug
from common import *
import numpy as np
from langchain_experimental.llms.ollama_functions import OllamaFunctions
from langchain_anthropic import ChatAnthropic
import time
import getpass
from langchain_groq import ChatGroq

set_debug(False)


def run(params_dict, input, optimal, model, max_iterations=3, self_debug=True):
    iters = 0
    no_run_time_error = False
    accu_solution = False

    if model.startswith("gpt"):
        llm = ChatOpenAI(model=model, temperature=0.0, verbose=True)
    elif model.startswith("claude"):
        llm = ChatAnthropic(model=model,
                            temperature=0.0, max_tokens=5000)
    elif model.startswith("llama"):
        llm = ChatGroq(
            model=model,
            temperature=0,
            max_tokens=None
        )

    pm = """
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


    prompt_template_gen = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an expert in Python programming for vehicle routing problems. You are good at calling {solver} in Python and solving problems."""
            ),
            ("user",
             pm
             ),
            ("placeholder", "{messages}")
        ]
    )


    prompt_template_debugger = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an expert in Python programming for vehicle routing problems by calling {solver}. Now your responsibility is to debug the code snippet with errors."""
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

    chain_1 = prompt_template_gen | llm.with_structured_output(code)
    chain_2 = prompt_template_debugger | llm.with_structured_output(code)

    result = chain_1.invoke(input)

    state = GraphState(error='', messages=[], generation=result, iterations=iters)
    state = code_check(state, params_dict, optimal)
    print("======== episode=" + str(int(iters)) + "=========")
    print(state)
    while iters < max_iterations:
        if state['error'] != 'no':
            message = state['messages']
            if len(message[0]) > 1:
                if ("The obj. is far from the optimum" in message[0][1]
                        or "You did not finish the function" in message[0][1] or "You solution returns nothing or 0" in message[0][1]):
                    print("no_run_time_error, but the solution is not accurate")
                    no_run_time_error = True
                if self_debug:
                    res = chain_2.invoke(
                        {'solver': 'OR-tools', 'prep_code': state['generation'].imports + "\n" + state['generation'].code,
                         'message': state['messages']})
                else:
                    res = chain_1.invoke(input)
                state = GraphState(error='', messages=[], generation=res, iterations=iters)
                state = code_check(state, params_dict, optimal)
                iters += 1
                print("======== episode=" + str(int(iters)) + "=========")
                print(state)
                if state['error'] == 'no':
                    print("---DONE---")
                    no_run_time_error = True
                    accu_solution = True
                    break
            if state['error'] == 'no':
                no_run_time_error = True
                accu_solution = True
                return no_run_time_error, accu_solution
        else:
            no_run_time_error = True
            accu_solution = True
            return no_run_time_error, accu_solution
    return no_run_time_error, accu_solution

if __name__ == "__main__":
    name, params, inputs, optimums = get_dataset()
    succ_metric = 0
    acc_tasks = []
    re_tasks = []
    metric_dict = {}
    name, params, inputs, optimums = name[25:], params[25:], inputs[25:], optimums[25:]
    for i in range(len(name)):
        print("-----Testing task: " + name[i] + "-----")
        # inputs[i]['solver'] = "Gurobi"
        # if name[i] in succed_tasks:
        #     print("Skip the task: " + name[i])
        #     continue
        inputs[i]['optimum'] = optimums[i]
        # try:
        no_run_time_error, accu = run(params[i], inputs[i], optimums[i])
        if not no_run_time_error:
            re_tasks.append(name[i])
        if accu:
            succ_metric += 1
            acc_tasks.append(name[i])
        # except:
        #     re_tasks.append(name[i])
        #     print("Error in task: " + name[i])
    print("-----Testing {:d} problems in total, and accurate rate is {:.4f}, runtime error rate is {:.4f}----".format(len(name), len(acc_tasks)/len(name), len(re_tasks)/len(name)))

# claude-3-5-sonnet-20241022 (or-tools): 22.92% - 41.67%

# accu4, re11