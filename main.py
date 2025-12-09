from dotenv import load_dotenv
from experiment import Experiment
from experiments.mystery_math import config as mystery_math_config
from experiments.reward_hacking import config as reward_hacking_config
from experiments.reward_hacking_xai import config as reward_hacking_xai_config
from experiments.reward_hacking_gpt_5 import config as reward_hacking_gpt_5_config
from experiments.whistleblower import config as whistleblower_config
from experiments.lazy_capable import config as lazy_capable_config
from experiments.marshmellow_test_tool import config as marshmellow_test_tool_config
load_dotenv()

def main():
    experiment = Experiment(
        name="Marshmallow Test Tool",
        directory=marshmellow_test_tool_config.DIRECTORY,
        model=marshmellow_test_tool_config.MODEL,
        system_prompt=marshmellow_test_tool_config.SYSTEM_PROMPT,
        task=marshmellow_test_tool_config.TASK,
        tools=marshmellow_test_tool_config.TOOLS,
        evals=marshmellow_test_tool_config.EVALS,
        max_attempts=marshmellow_test_tool_config.MAX_ATTEMPTS
    )
    # experiment = Experiment(
    #     name="Lazy Capable",
    #     directory=lazy_capable_config.DIRECTORY,
    #     model=lazy_capable_config.MODEL,
    #     system_prompt=lazy_capable_config.SYSTEM_PROMPT,
    #     task=lazy_capable_config.TASK,
    #     tools=lazy_capable_config.TOOLS,
    #     evals=lazy_capable_config.EVALS,
    # 
    # experiment = Experiment(
    #     name="Whistleblower",
    #     directory=whistleblower_config.DIRECTORY,
    #     model=whistleblower_config.MODEL,
    #     system_prompt=whistleblower_config.SYSTEM_PROMPT,
    #     task=whistleblower_config.TASK,
    #     tools=whistleblower_config.TOOLS,
    #     evals=whistleblower_config.EVALS,
    # )
    # experiment = Experiment(
    #     name="Reward Hacking GPT 5",
    #     directory=reward_hacking_gpt_5_config.DIRECTORY,
    #     model=reward_hacking_gpt_5_config.MODEL,
    #     system_prompt=reward_hacking_gpt_5_config.SYSTEM_PROMPT,
    #     task=reward_hacking_gpt_5_config.TASK,
    #     tools=reward_hacking_gpt_5_config.TOOLS,
    #     evals=reward_hacking_gpt_5_config.EVALS,
    #     max_attempts=reward_hacking_gpt_5_config.MAX_ATTEMPTS
    # )

    # experiment = Experiment(
    #     name="Reward Hacking",
    #     directory=reward_hacking_config.DIRECTORY,
    #     model=reward_hacking_config.MODEL,
    #     system_prompt=reward_hacking_config.SYSTEM_PROMPT,
    #     task=reward_hacking_config.TASK,
    #     tools=reward_hacking_config.TOOLS,
    #     evals=reward_hacking_config.EVALS,
    #     max_attempts=reward_hacking_config.MAX_ATTEMPTS
    # )

    # experiment = Experiment(
    #     name="Reward Hacking Xai",
    #     directory=reward_hacking_xai_config.DIRECTORY,
    #     model=reward_hacking_xai_config.MODEL,
    #     system_prompt=reward_hacking_xai_config.SYSTEM_PROMPT,
    #     task=reward_hacking_xai_config.TASK,
    #     tools=reward_hacking_xai_config.TOOLS,
    #     evals=reward_hacking_xai_config.EVALS,
    #     max_attempts=reward_hacking_xai_config.MAX_ATTEMPTS
    # )
    
    experiment.run_sequential(marshmellow_test_tool_config.IS_COMPLETE)

if __name__ == "__main__":
    main()
