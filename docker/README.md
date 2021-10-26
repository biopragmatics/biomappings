# Running Biomappings via Docker for curation

## 1. Fork the Biomappings repository

To preform curations using the Biomappings web interface, and contribute these
back through GitHub, you first have to fork the Biomappings repository as
follows:

1. Go to https://github.com/biopragmatics/biomappings
2. Click on the Fork button in the right upper corner of the page. Assuming your
   username is `GITHUBUSER`, this will create a forked repository at
   https://github.com/GITHUBUSER/biomappings.

See also the
GitHub [Fork a Repo](https://docs.github.com/en/get-started/quickstart/fork-a-repo)
tutorial.

## 2. Run the Biomappings Docker

Since contributions are pushed to GitHub, when running the Docker locally, the
Docker needs to have (read only) access to:

- The host machine's git configuration (which contains the name and email of the
  contributor) and is typically stored in `~/.gitconfig`
- The host machine's SSH key which provides push access to GITHUBUSER's fork of
  the Biomappings repo. This is typically stored in the `~/.ssh` folder. If you
  don't have one already, follow GitHub's guide
  to [making an SSH key](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account)

In the run command below, these two paths are mounted into the container.
Further, the `GITHUBUSER` value described above has to be provided as an
environment variable.

```shell
docker run -it -p 5000:5000 -v ~/.ssh:/root/.ssh:ro -v ~/.gitconfig:/root/.gitconfig:ro -e GITHUBUSER=<GITHUBUSER> biomappings:latest
```

Add `-d` to detach.

## 3. Launch the website and curate

Once the Docker container is running, you can open a browser and go to
http://localhost:5000, and start curating. Once done with a batch of curations,
click on the Commit button to have these committed and pushed to the `curation`
branch of https://github.com/GITHUBUSER/biomappings.

## 4. Submit a pull request

To contribute curations back to the main Biomappings repository, go
to https://github.com/biopragmatics/biomappings, and open a pull request from
the GITHUBUSER/curation branch.

# Building the docker image

To build the image, run the following

```shell
docker build --tag biomappings:latest .
```
