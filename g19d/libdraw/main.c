#include <stdint.h>
#include <stdio.h>
#include <byteswap.h>

#define PY_SSIZE_T_CLEAN
#include <Python.h>

/* TODO: Remove magic screen size G19_HEIGHT*G19_WIDTH */

#define G19_WIDTH 320
#define G19_HEIGHT 240
#define G19_RESOLUTION (G19_HEIGHT * G19_WIDTH)
#define G19_SIZE (G19_RESOLUTION * sizeof(uint16_t))
#define G19_PIXEL(_x, _y) ((_x) * G19_HEIGHT + (_y))

typedef struct {
	PyObject_HEAD
	uint16_t * map;
} g19_frame_t;

static PyObject * g19_get_bytes(g19_frame_t * self, PyObject * Py_UNUSED(ignored))
{
	PyObject * result = PyBytes_FromStringAndSize((const char *)self->map, G19_SIZE);
	return result;
}

static inline uint16_t _rgb_to_uint16(uint8_t red, uint8_t green, uint8_t blue)
{
	uint8_t red_bits =   ((uint8_t)(red   * (0b00011111 / 255.)) & 0b00011111);
	uint8_t green_bits = ((uint8_t)(green * (0b00111111 / 255.)) & 0b00111111);
	uint8_t blue_bits =  ((uint8_t)(blue  * (0b00011111 / 255.)) & 0b00011111);

	return red_bits << 11 | green_bits << 5 | blue_bits;
}

static PyObject * rgb_to_uint16(PyObject * self, PyObject *args)
{
	uint8_t red   = 0,
	        green = 0,
	        blue  = 0;

	if(!PyArg_ParseTuple(args, "bbb", &red, &green, &blue))
		return NULL;

	return Py_BuildValue("I", _rgb_to_uint16(red, green, blue));
}

static inline uint16_t _apply_alpha(uint16_t color1, uint16_t color2, float alpha)
{
	if (alpha == 1.)
		return color2;
	else if (alpha == 0.)
		return color1;

	uint8_t red1 = color1 >> 11 & 0b00011111;
	uint8_t red2 = color2 >> 11 & 0b00011111;
	uint8_t green1 = color1 >> 5 & 0b00111111;
	uint8_t green2 = color2 >> 5 & 0b00111111;
	uint8_t blue1 = color1 & 0b00011111;
	uint8_t blue2 = color2 & 0b00011111;

	uint8_t red_bits = (uint8_t)(red2 * alpha + red1 * (1 - alpha)) & 0b00011111;
	uint8_t green_bits = (uint8_t)(green2 * alpha + green1 * (1 - alpha)) & 0b00111111;
	uint8_t blue_bits = (uint8_t)(blue2 * alpha + blue1 * (1 - alpha)) & 0b00011111;

	return red_bits << 11 | green_bits << 5 | blue_bits;
}

static PyObject * apply_alpha(PyObject * self, PyObject *args)
{
	uint16_t color1 = 0,
	         color2 = 0;
	float alpha = 0.;

	if(!PyArg_ParseTuple(args, "HHf", &color1, &color2, &alpha))
		return NULL;

	return Py_BuildValue("I", _apply_alpha(color1, color2, alpha));
}

static PyObject * draw_rectangle(g19_frame_t * self, PyObject * args)
{
	int x  = 0,
	    y  = 0,
	    sx = 0,
	    sy = 0;

	uint16_t color = 0;
	float alpha = 0.;

	if(!PyArg_ParseTuple(args, "iiiiHf", &x, &y, &sx, &sy, &color, &alpha))
		return NULL;

	int end_x = x + sx;
	if (end_x > G19_WIDTH)
		end_x = G19_WIDTH;

	int end_y = y + sy;
	if (end_y > G19_HEIGHT)
		end_y = G19_HEIGHT;

	for (int px = x; px < end_x; px++)
	{
		for (int py = y; py < end_y; py++)
			self->map[G19_PIXEL(px, py)] = _apply_alpha(self->map[G19_PIXEL(px, py)], color, alpha);
	}

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject * copy_rectangle(g19_frame_t * self, PyObject * args)
{
	PyObject * bsrc   = NULL,
	         * balpha = NULL;
	int x  = 0,
	    y  = 0,
	    sx = 0,
	    sy = 0;

	if(!PyArg_ParseTuple(args, "iiiiSS", &x, &y, &sx, &sy, &bsrc, &balpha))
		return NULL;

	char * src = PyBytes_AsString(bsrc);

	char * alpha = PyBytes_AsString(balpha);

	int end_x = x + sx;

	int end_y = y + sy;

	uint16_t * img = (uint16_t *)src;
	uint8_t * mask = (uint8_t *)alpha;
	int img_idx = 0;

	for (int py = y; py < end_y; py++)
	{
		if (py < 0 || py >= G19_HEIGHT)
		{
			img_idx += sx;
			continue;
		}
		for (int px = x; px < end_x; px++)
		{
			if (px >= 0 && px < G19_WIDTH)
				self->map[G19_PIXEL(px, py)] = _apply_alpha(self->map[G19_PIXEL(px, py)], img[img_idx],
				                                            (float)mask[img_idx] / 255);
			img_idx++;
		}
	}

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject * copy_text(g19_frame_t * self, PyObject * args)
{
	PyObject * balpha = NULL;

	int x  = 0,
	    y  = 0,
	    sx = 0,
	    sy = 0;

	uint16_t color;

	if(!PyArg_ParseTuple(args, "iiiiHS", &x, &y, &sx, &sy, &color, &balpha))
		return NULL;

	char * alpha = PyBytes_AsString(balpha);

	int end_x = x + sx;

	int end_y = y + sy;

	uint8_t * mask = (uint8_t *)alpha;
	int idx = 0;

	for (int py = y; py < end_y; py++)
	{
		if (py < 0 || py >= G19_HEIGHT)
		{
			idx += sx;
			continue;
		}
		for (int px = x; px < end_x; px++)
		{
			if (px >= 0 && px < G19_WIDTH)
				self->map[G19_PIXEL(px, py)] = _apply_alpha(self->map[G19_PIXEL(px, py)], color,
			                                               (float)mask[idx] / 255);
			idx++;
		}
	}

	Py_INCREF(Py_None);
	return Py_None;
}

static PyMethodDef LibCDrawMethods[] = {
	{"rgb_to_uint16", rgb_to_uint16, METH_VARARGS, "Convert 3x1-byte color's channel to 2-byte color"},
	{"apply_alpha", apply_alpha, METH_VARARGS, "Merge two pixel"},
	{NULL, NULL, 0, NULL}
};

static struct PyModuleDef libcdrawmodule = {
	PyModuleDef_HEAD_INIT,
	"libdrawc",
	"Drawer for G19-Linux-Driver",
	-1,
	LibCDrawMethods
};

static void g19_dealloc(g19_frame_t * self)
{
	free(self->map);
	Py_TYPE(self)->tp_free((PyObject *)self);
}

static int g19_init(g19_frame_t * self, PyObject * args, PyObject * kwds)
{
	self->map = calloc(sizeof(uint16_t), G19_RESOLUTION);
	if (!self->map)
		return -1;

	return 0;
}

static PyMethodDef g19_methods[] = {
	{"get_bytes", (PyCFunction)g19_get_bytes, METH_NOARGS, "Get map in bytes"},
	{"draw_rectangle", (PyCFunction)draw_rectangle, METH_VARARGS, "Draw rectangle on map"},
	{"copy_text", (PyCFunction)copy_text, METH_VARARGS, "Copy rectangle from 1-channel+alpha picture"},
	{"copy_rectangle", (PyCFunction)copy_rectangle, METH_VARARGS, "Copy rectangle from BGR pillow picture to map"},
	{NULL, NULL, 0, NULL}
};


static PyTypeObject g19_frame = {
	PyVarObject_HEAD_INIT(NULL, 0)
	.tp_name = "libcdraw.Frame",
	.tp_doc = "G19 Frame",
	.tp_basicsize = sizeof(g19_frame_t),
	.tp_itemsize = 0,
	.tp_flags = Py_TPFLAGS_DEFAULT,
	.tp_new = PyType_GenericNew,
	.tp_init = (initproc)g19_init,
	.tp_dealloc = (destructor)g19_dealloc,
	.tp_methods = g19_methods
};

PyMODINIT_FUNC PyInit_libcdraw(void)
{
	if (PyType_Ready(&g19_frame) < 0)
		return NULL;

	PyObject * module = PyModule_Create(&libcdrawmodule);
	if (module == NULL)
		return NULL;

	Py_INCREF(&g19_frame);
	if (PyModule_AddObject(module, "Frame", (PyObject *)&g19_frame) < 0)
	{
		Py_DECREF(&g19_frame);
		Py_DECREF(module);
		return NULL;
	}

	return module;
}

