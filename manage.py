#!/usr/bin/env python
# -*- coding: $utf-8 -*-


import json
import os
import subprocess
from pathlib import Path

import click
import yaml

from commons.aws.ssm_helper import get_parameters_by_path


def _print_block(string):
    click.echo(click.style("\n" + "*" * (len(string) + 4), fg="yellow"))
    click.echo(click.style("* " + string + " *", fg="yellow"))
    click.echo(click.style("*" * (len(string) + 4) + "\n", fg="yellow"))


def _get_all_parameters(current_stage):

    # Get all the params for posifi
    parameters = get_parameters_by_path('/posifi/')
    stages = ['prod', 'test', 'dev']

    # Default stage to 'dev'
    if current_stage not in stages:
        current_stage = 'dev'

    # Move all the stage-specific settings to the root
    if current_stage in parameters:
        for key in parameters[current_stage]:
            if key in parameters:
                parameters[key].update(parameters[current_stage][key])
            else:
                parameters[key] = parameters[current_stage][key]

    # Delete the settings under any stage
    for stage in stages:
        if stage in parameters:
            del parameters[stage]

    return parameters


def _download_settings_from_ssm(stage, file_name='settings.json', include_commit_hash=False):
    _print_block(
        f'Downloading setting params from SSM Parameter Store for stage "{stage}"')

    # get parameters and secrets from SSM
    parameters = _get_all_parameters(stage)

    # get commit hash and add it to the params
    if include_commit_hash:
        commit_hash = os.popen('git rev-parse HEAD').read().strip()
        parameters.update({'commit_hash': commit_hash})

    # save settings and secrets into a settings JSON file
    settings_json = {
        'parameters': parameters
    }
    file_path = Path('./commons') / file_name
    with file_path.open("w", encoding="utf-8") as file:
        json.dump(settings_json, file, indent=4)


@click.group()
def manage():
    pass


@manage.group()
def posifi():
    pass


@manage.command()
@click.option("-s", "--stage")
def download_params(stage):
    _download_settings_from_ssm(stage, include_commit_hash=True)
    click.echo(click.style(
        f"\nOK - '{stage}' params were succesfully downloaded\n", fg="green"))


@posifi.command(name="deploy")
@click.option("-f", "--function-name", help="function name")
@click.option("-s", "--stage", default="dev", help="Stage ['dev'(def), 'prod']")
@click.option("-i", "--import_settings", default=False, help="Import [true, false]")
def deploy_api(function_name, stage, import_settings):

    if import_settings:
        _download_settings_from_ssm(stage, include_commit_hash=True)

    _check_requirements()

    if function_name is None:
        _print_block(f"Deploying stage {stage}")
        os.system(f"sls deploy -s {stage}")

    elif function_name == 'all':
        _print_block(f"Deploying all functions to stage {stage}")

        with open("serverless.yml") as serverles_yml:
            serverless_data = yaml.load(serverles_yml)

        defined_functions = serverless_data.get("functions", {}).keys()

        processes = [
            subprocess.Popen(
                f"sls deploy -s {stage} -f {function_name}".split(' '))
            for function_name in defined_functions
        ]

        for process in processes:
            process.wait()

    else:
        _print_block(f"Deploying function {function_name} to stage {stage}")
        os.system(f"sls deploy -s {stage} -f {function_name}")

    _print_block(f"Deploy process completed")


def _check_requirements():
    new_requirements = os.popen("pipenv lock --requirements").read()
    old_requirements = []

    try:
        with open('.requirements.lock', 'r') as requirements:
            old_requirements = requirements.read()
    except Exception:
        pass

    if new_requirements != old_requirements:
        _print_block("Requirements differ, packaging new requirements...")

        with open('.requirements.lock', 'w') as requirements:
            requirements.write(new_requirements)

        os.system(f"rm -r .requirements")

        os.system("docker run -v \"$PWD\":/var/task -it lambci/lambda:build-python3.7 "
                  "pip install v -r .requirements.lock -t .requirements")

        os.system(
            'find .requirements -name "*.py[c|o]" -delete -empty -or -name "*.dist-info*" -exec rm -r "{}" \; -or -name "*__pycache__*" -delete')


if __name__ == "__main__":
    manage()
