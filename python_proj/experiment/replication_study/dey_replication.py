from csv import reader

# The number of PRs in the ecosystem.
# The ratio of accepted PRs in the ecosystem.
# The whether they have contributed to a project that is dependent on the focal project.





headers = ['ID', 'Platform', 'Name', 'Created Timestamp', 'Updated Timestamp', 'Description', 'Keywords', 'Homepage URL', 'Licenses', 'Repository URL', 'Versions Count', 'SourceRank', 'Latest Release Publish Timestamp', 'Latest Release Number', 'Package Manager ID', 'Dependent Projects Count', 'Language', 'Status', 'Last synced Timestamp', 'Dependent Repositories Count', 'Repository ID', 'Repository Host Type', 'Repository Name with Owner', 'Repository Description', 'Repository Fork?', 'Repository Created Timestamp', 'Repository Updated Timestamp', 'Repository Last pushed Timestamp', 'Repository Homepage URL', 'Repository Size', 'Repository Stars Count', 'Repository Language', 'Repository Issues enabled?', 'Repository Wiki enabled?', 'Repository Pages enabled?', 'Repository Forks Count', 'Repository Mirror URL', 'Repository Open Issues Count', 'Repository Default branch', 'Repository Watchers Count', 'Repository UUID', 'Repository Fork Source Name with Owner', 'Repository License', 'Repository Contributors Count', 'Repository Readme filename', 'Repository Changelog filename', 'Repository Contributing guidelines filename', 'Repository License filename', 'Repository Code of Conduct filename', 'Repository Security Threat Model filename', 'Repository Security Audit filename', 'Repository Status', 'Repository Last Synced Timestamp', 'Repository SourceRank', 'Repository Display Name', 'Repository SCM type', 'Repository Pull requests enabled?', 'Repository Logo URL', 'Repository Keywords']




repo_name_index = headers.index("Repository Name with Owner")
is_fork_index = headers.index("Repository Fork?")



with open("./data/libraries/npm-libraries-1.6.0-2020-01-12/projects_with_repository_fields-1.6.0-2020-01-12.csv", "r") as input_file:
    csv_reader = reader(input_file)
    count = 0
    for entry in csv_reader:
        count += 1
        is_frok = entry[is_fork_index]
        print(is_frok)
print(count)
