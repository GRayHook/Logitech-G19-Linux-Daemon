#include <stdint.h>
#include <stdio.h>
#include <byteswap.h>

#define PY_SSIZE_T_CLEAN
#include <Python.h>

/* TODO: Remove magic screen size 240*320 */

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

static PyObject * draw_rectangle(PyObject * self, PyObject * args)
{
	PyObject * bmap = NULL;

	int x  = 0,
	    y  = 0,
	    sx = 0,
	    sy = 0;

	uint16_t color = 0;
	float alpha = 0.;

	if(!PyArg_ParseTuple(args, "SiiiiHf", &bmap, &x, &y, &sx, &sy, &color, &alpha))
		return NULL;

	char * map = PyBytes_AsString(bmap);
	int map_size = PyBytes_Size(bmap);

	char * buf = calloc(sizeof(uint8_t), map_size);
	memcpy(buf, map, map_size);
	uint16_t * result = (uint16_t *)buf;

	int end_x = x + sx;
	int end_y = y + sy;
	uint16_t * pixels = (uint16_t *)map;

	for (int px = x; px < end_x; px++)
	{
		for (int py = y; py < end_y; py++)
			result[px * 240 + py] = _apply_alpha(pixels[px * 240 + py], color, alpha);
	}

	PyObject * result_obj = PyBytes_FromStringAndSize(buf, map_size);
	free(buf);
	return result_obj;
}

static PyObject * copy_rectangle(PyObject * self, PyObject * args)
{
	PyObject * bmap   = NULL,
	         * bsrc   = NULL,
	         * balpha = NULL;
	int x  = 0,
	    y  = 0,
	    sx = 0,
	    sy = 0;

	if(!PyArg_ParseTuple(args, "SiiiiSS", &bmap, &x, &y, &sx, &sy, &bsrc, &balpha))
		return NULL;

	char * map = PyBytes_AsString(bmap);
	int map_size = PyBytes_Size(bmap);

	char * buf = calloc(sizeof(uint8_t), map_size);
	memcpy(buf, map, map_size);
	uint16_t * result = (uint16_t *)buf;

	char * src = PyBytes_AsString(bsrc);

	char * alpha = PyBytes_AsString(balpha);

	int end_x = x + sx;
	int end_y = y + sy;
	uint16_t * pixels = (uint16_t *)map;
	uint16_t * img = (uint16_t *)src;
	uint8_t * mask = (uint8_t *)alpha;
	int mask_idx = 0;
	int img_idx = 0;

	for (int py = y; py < end_y; py++)
	{
		for (int px = x; px < end_x; px++)
		{
			result[px * 240 + py] = _apply_alpha(pixels[px * 240 + py], img[img_idx++],
			                                     (float)mask[mask_idx++] / 255);
		}
	}

	PyObject * result_obj = PyBytes_FromStringAndSize(buf, map_size);
	free(buf);
	return result_obj;
}

static PyObject * copy_text(PyObject * self, PyObject * args)
{
	PyObject * bmap   = NULL,
	         * balpha = NULL;

	int x  = 0,
	    y  = 0,
	    sx = 0,
	    sy = 0;

	uint16_t color;

	if(!PyArg_ParseTuple(args, "SiiiiHS", &bmap, &x, &y, &sx, &sy, &color, &balpha))
		return NULL;

	char * map = PyBytes_AsString(bmap);
	int map_size = PyBytes_Size(bmap);

	char * buf = calloc(sizeof(uint8_t), map_size);
	memcpy(buf, map, map_size);
	uint16_t * result = (uint16_t *)buf;

	char * alpha = PyBytes_AsString(balpha);

	int end_x = x + sx;
	int end_y = y + sy;
	uint16_t * pixels = (uint16_t *)map;
	uint8_t * mask = (uint8_t *)alpha;
	int idx = 0;

	for (int py = y; py < end_y; py++)
	{
		for (int px = x; px < end_x; px++)
		{
			result[px * 240 + py] = _apply_alpha(pixels[px * 240 + py], color,
			                                     (float)mask[idx++] / 255);
		}
	}

	PyObject * result_obj = PyBytes_FromStringAndSize(buf, map_size);
	free(buf);
	return result_obj;
}

static PyMethodDef LibCDrawMethods[] = {
	{"rgb_to_uint16", rgb_to_uint16, METH_VARARGS, "drisnya"},
	{"apply_alpha", apply_alpha, METH_VARARGS, "drisnya"},
	{"draw_rectangle", draw_rectangle, METH_VARARGS, "drisnya"},
	{"copy_text", copy_text, METH_VARARGS, "drisnya"},
	{"copy_rectangle", copy_rectangle, METH_VARARGS, "drisnya"},
	{NULL, NULL, 0, NULL}
};

static struct PyModuleDef libcdrawmodule = {
	PyModuleDef_HEAD_INIT,
	"libdrawc",
	"Drisnya",
	-1,
	LibCDrawMethods
};

PyMODINIT_FUNC PyInit_libcdraw(void)
{
	return PyModule_Create(&libcdrawmodule);
}
