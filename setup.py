from setuptools import setup

import versioneer

setup(
      name='extensor_vazoes',
      version=versioneer.get_version(),
      cmdclass=versioneer.get_cmdclass(),
      author="COPEL",
      packages=["extensor_vazoes"],
      url="https://gitprd.copel.nt/cppc/estudos/extensor_vazoes",
      python_requires=">=3.9",
      install_requires=["pandas>=1.4", "tqdm"],
)
