import warnings

try:
    from unittest.case import _ExpectedFailure as ExpectedFailure, _UnexpectedSuccess as UnexpectedSuccess
except ImportError:
    from unittest2.case import _ExpectedFailure as ExpectedFailure, _UnexpectedSuccess as UnexpectedSuccess

def install_proxy():
    import nose.proxy

    class MyResultProxy(nose.proxy.ResultProxy):
        def addExpectedFailure(self, test, err):
            #from nose.plugins.expected import ExpectedFailure
            self.assertMyTest(test)
            plugins = self.plugins
            plugins.addError(self.test, (ExpectedFailure, err, None))
            addExpectedFailure = getattr(self.result, "addExpectedFailure", None)
            if addExpectedFailure:
                self.result.addExpectedFailure(self.test, self._prepareErr(err))
            else:
                warnings.warn("TestResult has no addExpectedFailure method, reporting as passes",
                              RuntimeWarning)
                self.result.addSuccess(self)

        def addUnexpectedSuccess(self, test):
            #from nose.plugins.expected import UnexpectedSuccess
            self.assertMyTest(test)
            plugins = self.plugins
            plugins.addError(self.test, (UnexpectedSuccess, None, None))
            self.result.addUnexpectedSuccess(self.test)
            if self.config.stopOnError:
                self.shouldStop = True
    nose.proxy.ResultProxy = MyResultProxy

def install_result():
    import nose.result

    class MyTextTestResult(nose.result.TextTestResult):
        def addExpectedFailure(self, test, err):
            # 2.7 expected failure compat
            if ExpectedFailure in self.errorClasses:
                storage, label, isfail = self.errorClasses[ExpectedFailure]
                storage.append((test, self._exc_info_to_string(err, test)))
                self.printLabel(label, (ExpectedFailure, '', None))

        def addUnexpectedSuccess(self, test):
            # 2.7 unexpected success compat
            if UnexpectedSuccess in self.errorClasses:
                storage, label, isfail = self.errorClasses[UnexpectedSuccess]
                storage.append((test, 'This test was marked as an expected '
                    'failure, but it succeeded.'))
                self.printLabel(label, (UnexpectedSuccess, '', None))
    nose.result.TextTestResult = MyTextTestResult
