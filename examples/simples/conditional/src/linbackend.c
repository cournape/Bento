#include <Python.h>

static PyMethodDef LinuxBackendMethods[] = {
    {NULL, NULL, 0, NULL}        /* Sentinel */
};

PyMODINIT_FUNC
init_linux_backend(void)
{
    (void) Py_InitModule("_linux_backend", LinuxBackendMethods);
}
