

with open("./testfile.txt", 'w+') as test_file:
    test_file.write("asdfasdf")
    test_file.write("asdfasdf")
    test_file.write("asdfasdf")
    test_file.write("asdfasdf")
    test_file.write("asdfasdf")

with open("./other_test_file.txt", "w+") as other_test_file:
    other_test_file.write("hallo\n")
    with open("./testfile.txt", "r") as input_file:
        other_test_file.writelines(input_file)

