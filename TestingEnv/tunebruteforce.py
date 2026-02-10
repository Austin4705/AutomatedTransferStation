from argparse import ArgumentParser
from ppo import train, val, make_env
import numpy as np
import torch


def sample_params(env_id):
    # For reference, you may not want to tune all the parameters
    epochsArray = [100, 250, 350, 500]
    gammaArray = [0.95, 0.999]
    gae_lambdaArray = [0.9, 1]
    lrArray = [3e-6, 3e-4]
    num_stepsArray = [128, 256, 512, 1024]
    minibatch_sizeArray = [16, 32, 64]
    clip_ratioArray = [0.1, 0.2, 0.3, 0.5]
    num_envsArray = [2, 4, 8, 16]
    ent_coefArray = [0, 1e-2, 1e-3, 1e-4]
    vf_coefArray = [0.25, 0.5, 1]
    seed = 42
    # Try every combination of parameters using nested loops
    best_reward = float('-inf')
    best_params = None
    
    for epochs in epochsArray:
        for gamma in gammaArray:
            for gae_lambda in gae_lambdaArray:
                for lr in lrArray:
                    for num_steps in num_stepsArray:
                        for minibatch_size in minibatch_sizeArray:
                            for clip_ratio in clip_ratioArray:
                                for num_envs in num_envsArray:
                                    for ent_coef in ent_coefArray:
                                        for vf_coef in vf_coefArray:
                                            # Try this parameter combination
                                            params = dict(
                                                epochs=epochs,
                                                gamma=gamma, 
                                                gae_lambda=gae_lambda,
                                                lr=lr,
                                                num_steps=num_steps,
                                                minibatch_size=minibatch_size,
                                                clip_ratio=clip_ratio,
                                                num_envs=num_envs,
                                                ent_coef=ent_coef,
                                                seed=seed,
                                                vf_coef=vf_coef
                                            )
                                            
                                            # Use GPU if available
                                            device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
                                            with torch.cuda.device(device):
                                                model = train(env_id, **params)
                                                env = make_env(env_id)()
                                                # Make sure model is on the right device for evaluation
                                                if hasattr(model, "to"):
                                                    model = model.to(device)
                                                reward = val(model, env, num_ep=100)
                                                print(reward, params)
                                                if reward > best_reward:
                                                    best_reward = reward
                                                    best_params = params.copy()
                                                    
                                            torch.cuda.empty_cache()
    
    return best_params

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--env_id", type=str, default="LunarLander-v2")
    # parser.add_argument("--env_id", type=str, default="Reacher-v4")
    parser.add_argument("--num_trials", type=int, default=100)
    args = parser.parse_args()
    for i in range(args.num_trials):
        train_args = sample_params(args.env_id)
        model = train(args.env_id, **train_args)
        env = make_env(args.env_id)()
        eval_rew = val(model, env, num_ep=100)
        print(eval_rew, train_args) 