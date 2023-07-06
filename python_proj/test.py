
class MyOtherClass:
    def __init__(self) -> None:
        self.some_cool_value = 0


class MyTestClass:
    def __init__(self, other_value: MyOtherClass) -> None:
        self.__other_val = other_value

    def fun(self):
        self.__other_val.some_cool_value += 1


myclass_a = MyOtherClass()

print(myclass_a.some_cool_value)
a = MyTestClass(myclass_a)
a.fun()
b = MyTestClass(myclass_a)
a.fun()
c = MyTestClass(myclass_a)
a.fun()

print(myclass_a.some_cool_value)
