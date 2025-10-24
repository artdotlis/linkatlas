# LinkAtlas - links between strains and taxonomy

[![release: 0.1.0](https://img.shields.io/badge/rel-0.1.0-blue.svg?style=flat-square)](https://gitlab.int.dsmz.de/artur.lissin/linkatlas#)
[![MIT LICENSE](https://img.shields.io/badge/License-MIT-brightgreen.svg?style=flat-square)](https://choosealicense.com/licenses/mit/)
[![Documentation Status](https://img.shields.io/badge/docs-GitHub-blue.svg?style=flat-square)](https://artdotlis.github.io/linkatlas/)

[![main](https://github.com/artdotlis/linkatlas/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/artdotlis/linkatlas/actions/workflows/main.yml)


---

A collection of libraries for gathering possible links between strains and taxonomy from different sources like literature and sequence databases.

## Installation - Development

### Prerequisites

- **GNU/Linux**
- **Docker (optional)**
- **Docker Compose (optional)**
- **Dev Container CLI (optional)**

### Steps

1. Clone the repository:
   ```sh
   git clone https://github.com/LeibnizDSMZ/cafi.git
   cd cafi
   ```

#### Docker

2. If using Docker, start the development container manually or use VSCode:
   ```sh
   devcontainer up --workspace-folder .
   devcontainer exec --workspace-folder . bash
   ```

3. Create and activate a virtual environment (inside docker the container):
   ```sh
   make dev
   make runAct
   ```

## Contributors

- Isabel Schober
