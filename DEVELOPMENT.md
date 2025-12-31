<!-- HEADER -->
<br id="top" />
<p align="center">
    <!-- <a href="#" target="_blank" rel="noopener noreferrer">
        <img src="#" width="48" />
    </a> -->
</p>
<h1 align="center">Development</h1>

This file provides guidance for getting started with your local development environment when working with code in this repository.

## Table of contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Environment setup](#environment-setup)
- [Environment startup](#environment-startup)
- [Commands](#commands)

## Overview

TODO

<p align="right">
  <sub><a href="#top">back to the top</a></sub>
</p>

## Architecture

TODO

<p align="right">
  <sub><a href="#top">back to the top</a></sub>
</p>

## Prerequisites

You will need to install [uv](https://docs.astral.sh/uv/getting-started/installation/) to manage Python versions, virtual environments and dependencies.

<p align="right">
  <sub><a href="#top">back to the top</a></sub>
</p>

## Environment setup

### Clone the repository to your local machine

```sh
git clone https://github.com/homer2011/sanityv2.git
cd sanityv2
```

### Environment variables

TODO

<p align="right">
  <sub><a href="#top">back to the top</a></sub>
</p>

## Environment startup

> [!TIP]
> Use multiple terminal tabs to run applications in parallel.

### Start backend

**1. Navigate to the application root directory**

```sh
cd apps/api
```

**2. Install Python dependencies**

```sh
uv sync
```

**3. Start the server**

```sh
uv run task dev
```

By default, the server will be available on port `8000`, and hot reload is enabled.

### Start frontend

TODO

<p align="right">
  <sub><a href="#top">back to the top</a></sub>
</p>

## Commands

### Backend development

```bash
uv sync                     # install dependencies

uv run task dev             # start the development server
```

### Frontend development

TODO

<!-- FOOTER -->
<p align="center">
  <sub><a href="#top">back to the top</a></sub>
</p>
