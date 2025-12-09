from dotenv import load_dotenv
from experiment import Experiment
load_dotenv()

def main():
    experiment = Experiment.load('marshmellow_test_tool')
    experiment.run()

if __name__ == "__main__":
    main()
