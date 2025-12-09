from dotenv import load_dotenv
from experiment import Experiment
load_dotenv()

def main():
    experiment = Experiment.load('lazy_capable')
    experiment.run()

if __name__ == "__main__":
    main()
