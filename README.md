## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

What things you need to install the software:

- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Installing

A step-by-step series of examples that tell you how to get a development environment running.

1. Clone the repository to your local machine:

    ```sh
    git clone https://github.com/SergeyDev1996/VpnTestTask.git
    ```

2. Navigate to the directory where you cloned the repository:
     ```sh
    cd path-to-your-project
    ```

3. Copy the env_template to the env file
    ```sh
    cp .env_template .env
    ```

4. Build and run the containers using Docker Compose:

    ```sh
    docker-compose up --build
    ```

    The `--build` flag is used to build the images before starting the containers.

5. Your project should now be running on [http://127.0.0.1:8050/](http://127.0.0.1:8050/) (or another port if you've configured it differently in your Docker settings).
## Creating a New Site



To add a new site to the system, follow these steps:
1. Create a new user at the (http://127.0.0.1:8050/user/signup/)
2. Go to the Create New Site page by clicking on the 'Create Site' button located on the 'Your Sites' page.

3. In the form provided, enter a unique name for the site in the 'Name' field. This should be an identifier that is easy for you to remember.

4. Enter the full URL of the site you wish to add in the 'URL' field, including the `http://` or `https://` prefix.
5. Click the 'Submit' button to create the site.
6. If you see any error messages, such as "A site with this name and URL already exists," correct the information accordingly and re-submit the form.
7. Once the site is successfully created, go to the list of sites and click "Proxy" button near you site. 