from setuptools import find_packages, setup

test_deps = [
    'pytest',
    'PyHamcrest',
    'requests-mock'
]

extras = {
    'test': test_deps,
}

setup(
    name='dsmlp-validator',
    extras_require=extras,
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    tests_require=test_deps,
)
