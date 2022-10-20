See the [qibo repo](https://github.com/qiboteam/qibo) for any details.

This is a prototype repo to enable jit-compilation of *qibo* using Jax.

To install this package, clone this repository:
```bash
git clone https://github.com/MSRudolph/qibo_jax.git
```
then navigate into the clone directory:
```bash
cd qibo_jax
```
and install the package in editable mode:
```bash
pip install -e .
```

Installation requirements are
- jax
- jaxlib
- flax

I am working with a sketchy Windows installation of Jax, so you might encounter errors. Additionally, the changes made to make Jax and *qibo* work are minimal. Most code is unusable so-far.

