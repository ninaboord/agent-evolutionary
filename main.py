# from experiment import Experiment
from dotenv import load_dotenv
load_dotenv()

# Original experiment code (commented out)
# def main():
#     experiment = Experiment.load('reward_hacking_bogus_test')
#     experiment.run()

# Evolutionary experiment
from evolutionary_main import main as evolutionary_main

def main():
    evolutionary_main()

if __name__ == "__main__":
    main()
