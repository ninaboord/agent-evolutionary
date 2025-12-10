from experiment import Experiment
from dotenv import load_dotenv
load_dotenv()

def main():
    experiment = Experiment.load('whistleblower')
    experiment.run()

if __name__ == "__main__":
    main()
