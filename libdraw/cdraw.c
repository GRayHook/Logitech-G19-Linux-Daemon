#include <Python.h>
#include <stdio.h>

uint16_t rgb_to_uint16(int * color_rgb)
{
	char red_bits = color_rgb[0] * 2 * 2 * 2 * 2 * 2 / 255;
	char green_bits = color_rgb[1] * 2 * 2 * 2 * 2 * 2 * 2 / 255;
	char blue_bits = color_rgb[2] * 2 * 2 * 2 * 2 * 2 / 255;

	red_bits = red_bits <= 0b00011111 ? red_bits : 0x00011111;
	green_bits = green_bits <= 0b00111111 ? green_bits : 0x00111111;
	blue_bits = blue_bits <= 0b00011111 ? blue_bits : 0x00011111;

	uint8_t value_high = (red_bits << 3) | (green_bits >> 3);
	uint16_t value_low = (green_bits << 5) | blue_bits;
	return value_low << 8 | value_high;
}

#define SCRHEIGHT 240
#define SCRWIDTH 320
uint16_t map[SCRHEIGHT * SCRWIDTH];

PyObject * set_map(PyObject * self, PyObject * args)
{
	PyObject * result = 0;
	char mystring[24] = "";

	PyObject * py_tuple;
	if (!PyArg_ParseTuple(args, "O!", &PyList_Type, &py_tuple)) {
		return NULL;
	}

	int len = PyList_Size(py_tuple);
	// map = malloc(len * sizeof(uint16_t));
	for (size_t i = 0; i < len; i++) {
		map[i] = (uint16_t) PyInt_AsLong(PyList_GetItem(py_tuple, i));
		sprintf(mystring + strlen(mystring), "(%u)", map[i]);
	}

	result = PyString_FromString("Hello ");
	PyString_Concat(&result, PyString_FromString(mystring));
	return result;
}

PyObject * get_map(PyObject * self, PyObject * args)
{
	PyObject * result = 0;
	char mystring[24] = "";

	PyObject * py_tuple;
	for (size_t i = 0; i < SCRWIDTH * SCRHEIGHT; i++) {
		
	}

	result = PyString_FromString("Hello ");
	PyString_Concat(&result, PyString_FromString(mystring));
	return result;
}

PyObject * set_point(PyObject * self, PyObject * args)
{
	PyObject * result = 0;
	char mystring[24] = "";

	PyObject * py_tuple;
	int len;
	uint16_t rgb;
	// uint16_t map[4];
	if (!PyArg_ParseTuple(args, "O!", &PyList_Type, &py_tuple)) {
		return NULL;
	}
	len = PyList_Size(py_tuple);
	map = malloc(len * sizeof(uint16_t));
	for (size_t i = 0; i < len; i++) {
		map[i] = (uint16_t) PyInt_AsLong(PyList_GetItem(py_tuple, i));
		sprintf(mystring + strlen(mystring), "(%u)", map[i]);
	}

	// column = self.__get_column(position[0])
	// index = column + position[1] * 2
	// uint_16_color = self.__rgb_to_uint16(color)
	//
	// if len(color) > 3:
	// 	old_pixel_uint16 = (self.__map[index] << 8) | self.__map[index + 1]
	// 	uint_16_color = self.__uint16_apply_alpha(old_pixel_uint16, uint_16_color, color[3])
	//
	// self.__map[index] = self.__value_low(uint_16_color)
	// self.__map[index + 1] = self.__value_high(uint_16_color)

	result = PyString_FromString("Hello ");
	PyString_Concat(&result, PyString_FromString(mystring));
	return result;
}

static PyMethodDef libcdraw_methods[] =
{
	{ "set_map", (PyCFunction) set_map, METH_VARARGS, "set_map(who) -- return \"Hello who\"" },
	{ "get_map", (PyCFunction) get_map, METH_VARARGS, "get_map(who) -- return \"Hello who\"" },
	{ "set_point", (PyCFunction) set_point, METH_VARARGS, "set_point(who) -- return \"Hello who\"" },
	{ NULL, 0, 0, NULL }
};


PyMODINIT_FUNC initlibcdraw()
{
	(void) Py_InitModule("libcdraw", libcdraw_methods);

	if (PyErr_Occurred())
	{
		PyErr_SetString(PyExc_ImportError, "libcdraw module init failed");
	}
}
