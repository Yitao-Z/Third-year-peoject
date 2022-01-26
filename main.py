import numpy as np
import env
import gym
import stable_baselines3
from stable_baselines3 import A2C
from stable_baselines3 import PPO
from stable_baselines3.common.results_plotter import load_results, ts2xy
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common import results_plotter
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.evaluation import evaluate_policy
from IPython.display import clear_output
import os


class SaveOnBestTrainingRewardCallback(BaseCallback):
    """
    Callback for saving a model (the check is done every ``check_freq`` steps)
    based on the training reward (in practice, we recommend using ``EvalCallback``).

    :param check_freq: (int)
    :param log_dir: (str) Path to the folder where the model will be saved.
      It must contains the file created by the ``Monitor`` wrapper.
    :param verbose: (int)
    """

    def __init__(self, check_freq: int, log_dir: str, verbose=1):
        super(SaveOnBestTrainingRewardCallback, self).__init__(verbose)
        self.check_freq = check_freq
        self.log_dir = log_dir
        self.save_path = os.path.join(log_dir, 'best_model')
        self.best_mean_reward = -np.inf

    def _init_callback(self) -> None:
        # Create folder if needed
        if self.save_path is not None:
            os.makedirs(self.save_path, exist_ok=True)

    def _on_step(self) -> bool:
        if self.n_calls % self.check_freq == 0:
            # Retrieve training reward
            x, y = ts2xy(load_results(self.log_dir), 'timesteps')
            if len(x) > 0:
                # Mean training reward over the last 100 episodes
                mean_reward = np.mean(y[-100:])
                if self.verbose > 0:
                    print("Num timesteps: {} - ".format(self.num_timesteps), end="")
                    print(
                        "Best mean reward: {:.2f} - Last mean reward per episode: {:.2f}".format(self.best_mean_reward,
                                                                                                 mean_reward))
                # New best model, you could save the agent here
                if mean_reward > self.best_mean_reward:
                    self.best_mean_reward = mean_reward
                    # Example for saving best model
                    if self.verbose > 0:
                        print("Saving new best model to {}".format(self.save_path))
                        self.model.save(self.save_path)
                if self.verbose > 0:
                    clear_output(wait=True)

        return True

# topology A
log_dir = "./tmp/network_Env-v0/"
os.makedirs(log_dir, exist_ok=True)
callback = SaveOnBestTrainingRewardCallback(check_freq=5000, log_dir=log_dir)

env_args = dict(episode_length=5000, load=1,
                mean_service_holding_time=10, k_paths=2)
the_env = gym.make('network_Env-v0', **env_args)
the_env = Monitor(the_env, log_dir + 'training', info_keywords=('P_accepted', 'topology_num',))

# topology B
env_args_2 = dict(episode_length=5000, load=1,
                  mean_service_holding_time=10, k_paths=2, topology_num=1)
the_env_2 = gym.make('network_Env-v0', **env_args_2)
the_env_2 = Monitor(the_env_2, log_dir + 'training', info_keywords=('P_accepted', 'topology_num',))

# create agent
model = A2C("MultiInputPolicy", the_env, verbose=1, device='cuda', gamma=0.7)
model.learn(total_timesteps=10000, callback=callback)
#eva = evaluate_policy(model, the_env, n_eval_episodes=10)
eva_2 = evaluate_policy(model, the_env_2, n_eval_episodes=10)
the_env.close()


