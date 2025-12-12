from experiment import Experiment
from evolutionary import EvolutionaryExperiment
from dotenv import load_dotenv

load_dotenv()

def run_standard_experiment():
    """Run a standard experiment."""
    experiment = Experiment.load('reward_hacking_bogus_test')
    experiment.run()

def run_evolutionary_experiment():
    """Run an evolutionary experiment."""
    experiment = EvolutionaryExperiment.load("the_marshmellow")
    experiment.evolve()

def main():
    # Uncomment one of these to run:
    # run_standard_experiment()
    run_evolutionary_experiment()

if __name__ == "__main__":
    main()
