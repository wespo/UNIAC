#class test
class classTest:
    class fooBar:
        def foo(self):
            print "foo"
        def bar(self):
            print "bar"
    def __init__(self):
        self.fb = fooBar()

ct = classTest()
ct.fb.foo()
