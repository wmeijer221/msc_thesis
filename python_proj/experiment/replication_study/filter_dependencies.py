from csv import reader, writer


filter_path = "./data/libraries/npm-libraries-1.6.0-2020-01-12/projects_with_repository_fields-1.6.0-2020-01-12_filtered.csv"
filter_file = open(filter_path, "r")
filter_reader = reader(filter_file)
filtered_projects = {entry[0] for entry in filter_reader}

dependency_path = "./data/libraries/npm-libraries-1.6.0-2020-01-12/repository_dependencies-1.6.0-2020-01-12.csv"
dependency_file = open(dependency_path, "r")
dependency_reader = reader(dependency_file)

filtered_dependency_path = "./data/libraries/npm-libraries-1.6.0-2020-01-12/repository_dependencies-1.6.0-2020-01-12_filtered.csv"
filtered_dependency_file = open(filtered_dependency_path, "w+")
filtered_dependency_writer = writer(filtered_dependency_file)

for entry in dependency_reader:
    if not entry[0] in filtered_projects or not entry[-1] in filtered_projects:
        continue
    filtered_dependency_writer.writerow(entry)
