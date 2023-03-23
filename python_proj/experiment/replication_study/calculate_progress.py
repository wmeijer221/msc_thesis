

from csv import reader
from sys import argv
import math
import numpy

from python_proj.experiment.util import safe_index


headers = ['ID', 'Platform', 'Name', 'Created Timestamp', 'Updated Timestamp', 'Description', 'Keywords', 'Homepage URL', 'Licenses', 'Repository URL', 'Versions Count', 'SourceRank', 'Latest Release Publish Timestamp', 'Latest Release Number', 'Package Manager ID', 'Dependent Projects Count', 'Language', 'Status', 'Last synced Timestamp', 'Dependent Repositories Count', 'Repository ID', 'Repository Host Type', 'Repository Name with Owner', 'Repository Description', 'Repository Fork?', 'Repository Created Timestamp', 'Repository Updated Timestamp', 'Repository Last pushed Timestamp', 'Repository Homepage URL', 'Repository Size', 'Repository Stars Count', 'Repository Language', 'Repository Issues enabled?', 'Repository Wiki enabled?',
           'Repository Pages enabled?', 'Repository Forks Count', 'Repository Mirror URL', 'Repository Open Issues Count', 'Repository Default branch', 'Repository Watchers Count', 'Repository UUID', 'Repository Fork Source Name with Owner', 'Repository License', 'Repository Contributors Count', 'Repository Readme filename', 'Repository Changelog filename', 'Repository Contributing guidelines filename', 'Repository License filename', 'Repository Code of Conduct filename', 'Repository Security Threat Model filename', 'Repository Security Audit filename', 'Repository Status', 'Repository Last Synced Timestamp', 'Repository SourceRank', 'Repository Display Name', 'Repository SCM type', 'Repository Pull requests enabled?', 'Repository Logo URL', 'Repository Keywords']

repo_name_index = headers.index("Repository Name with Owner")

file_path = "./data/libraries/npm-libraries-1.6.0-2020-01-12/projects_with_repository_fields-1.6.0-2020-01-12.csv"

if (p_index := safe_index(argv, "-p")) >= 0:
    project_names = str(argv[p_index + 1])
    print(f'Looking for \"{project_names}\".')

    projs: set = {entry.strip() for entry in project_names.split(",")}

    with open(file_path, "r", encoding="utf-8") as input_file:
        csv_reader = reader(input_file)
        count = 0
        targets = []
        for index, entry in enumerate(csv_reader, 1):
            count = index
            if entry[repo_name_index] in projs:
                targets.append(index)

    avg = numpy.average(targets)
    std = numpy.std(targets)

    perc = (avg / count) * 100
    perc_dev = (std / count) * 100
    print(
        f"Approximate progress: {avg}/{count} ({perc:3f}% +-{perc_dev}%), with {len(projs)=}, {len(targets)=}.")

    print(f'{targets=}')
