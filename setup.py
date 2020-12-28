import setuptools

c_module = setuptools.Extension('g19d.libcdraw',
                sources = ['g19d/libdraw/main.c'])

setuptools.setup(
    name="g19d",
    version="0.9.0",
    author="Sergey Marinkevich",
    author_email="s@marinkevich.ru",
    description="Logitech G19 userspace driver",
    packages=setuptools.find_packages(),
    python_requires='>=3.6',
    data_files = [
        ('g19d/logitech', ['g19d/logitech/logo']),
        ('g19d/libdraw', ['g19d/libdraw/11676.otf']),
        ('g19d', ['g19d/background.png', 'g19d/flake.png']),
    ],
    entry_points={
        "console_scripts": [
            "g19d = g19d.__main__:main"
        ]
    },
    ext_modules = [c_module]
)
