# Running Biomappings via Docker for curation

1. Fork the Biomappings repository

To preform curations using the Biomappings web interface, and contribute
these back through Github, you first have to fork the biomappings repository
as follows.

Go to https://github.com/biopragmatics/biomappings, and click on the Fork
button in the right upper corner of the page. Assuming your user name is
GITHUBUSER, this will create a forked repository at
https://github.com/GITHUBUSER/biomappings.

2. Run the Biomappings Docker

Since contributions are pushed to Github, when running the Docker locally,
the Docker needs to have (read only) access to:
- The host machine's git configuration (which contains the name and email of
the contributor) and is typically stored in ~/.gitconfig
- The host machine's SSH key which provides push access to GITHUBUSER's
fork of the biomappings repo. This is typically stored in the ~/.ssh folder.

In the run command below, these two paths are mounted into the container.
Further the GITHUBUSER value described above has to be provided as an
environment variable.

```
docker run -d -it -p 5000:5000 -v ~/.ssh:/root/.ssh:ro -v ~/.gitconfig:/root/.gitconfig:ro -e GITHUBUSER=<GITHUBUSER> biomappings:latest
```

3. Launch the website and curate

Once the Docker container is running, you can open a browser and go to
http://localhost:5000, and start curating. Once done with a batch of curations,
click on the Commit button to have these committed and pushed to
the `curation` branch of https://github.com/GITHUBUSER/biomappings.

4. Submit a pull request

To contribute curations back to the main Biomappings repository,
go to https://github.com/biopragmatics/biomappings, and open a
pull request from the GITHUBUSER/curation branch.

# Building the docker image

To build the image, run the following
```
docker build --tag biomappings:latest .
```
