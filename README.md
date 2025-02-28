# Webpage publishing using quarto

This material includes the webpage created with `Quarto` along with an automatic deployment script to make it into a live webpage. Further details can be found in the paragraphs following this introduction.

If you want to produce a webpage on your computer, you simply need to install [Quarto](https://quarto.org/docs/download/) and [Pandoc](https://pandoc.org/installing.html). Additionally, for using the `R` commands in this webpage example, you may optionally require the `R` packages `tidyverse, rmarkdown, knitr, gt`. If you plan to incorporate `R markdown` files to the webpage, ensure that you have the corresponding R packages for their code to function properly.

Following, you can read a small guide consisting of several steps:
- configuration file (`_quarto.yml`): specifies the project settings (metadata, dependencies, output formats, etc.)
- quarto Markdown file (`index.qmd`): main content file that will rendered into the final output, the website.
- additional files: `R markdown`, `Jupyter Notebooks` or any other content 
- push the changes to the Git repository and publish the webpage

## Configuration file

The setup file for your webpage is called `_quarto.yml`. This example provided here contains many commonly used configurations, but you can find links to various components to configure your website [here](https://quarto.org/docs/websites/).

### navigation bar

In our configuration, you will find the type of `project`, and the `website` descriptors. Within the `website`, there is a title and the configuration for the navigation bar (`navbar`), which defines the items for the left and right sides:

```yml
    left:
      - href: index.qmd
        text: Introduction
      - href: people.qmd
        text: People
      - href: rmd/rmarkdown_example.Rmd
        text: Rmarkdown      
      - href: jupyter_example.ipynb
        text: Jupyter example
    right: 
      - icon: github
        href: https://github.com/hds-sandbox
        aria-label: GitHub
      - icon: linkedin
        href: https://www.linkedin.com/company/ucph-heads/
        aria-label: LinkedIn
```
On the left side, we specify the menu titles and links to other documents used for the subpages. On the right side, there are a couple of icons with social media links. It is straightforward to add new pages to the menu on the left to change the structure of the website.

### themes

Below, you will find HTML themes for the webpage, available both in light and dark mode. We've customized the light mode theme to match the sandbox colors, using the `materia` theme with some elements modified using an 'scss' file.  The `scss` format is very easy to understand, allowing for effortless modification of other elements of the theme (though it should not be needed for a sandbox-style webpage). The dark theme is a standard one, and we  haven't attempted to match any sandbox color scheme. 

```yml
format:
  html:
    theme: 
      light: [materia, css/materialight.scss]
      dark: darkly
    toc: true
```

Check out [this link](https://quarto.org/docs/output-formats/html-themes.html) for more information on modifying a `scss` file with examples for `Quarto`.

### bioschemas

Finally, there is a commented-out section that includes a bioschema as part of the webpage header. The [bioschema](https://bioschemas.org/) is in an HTML file, whose script is always executed by the deployed webpage. 

!!! important
    Uncomment this part of the configuration **only upon finalization of your website** - so that it will be published on the Elixir TeSS database with the appropriate finished content.

Take a look at `resources/bioschema.html` to see how the bioschema is structured. It is essentially a `JSON` table containing standard descriptors such as course name, type, audience, datasets and more.

```json
    {
      "@context": "https://schema.org",
      "@id": "https://hds-sandbox.github.io/",
      "@type": "LearningResource",
      "dct:conformsTo": "https://bioschemas.org/profiles/TrainingMaterial/1.0-RELEASE",
      "description": "Home page of the danish health data science sandbox",
      "keywords": [
        "# Keyword1, Keyword2, etc"
      ],
      "learningResourceType": [
        "e-learning"
      ],
      "license": [
        {
          "@id": "https://creativecommons.org/licenses/by-sa/4.0/",
          "@type": "CreativeWork"
        }
      ],
      "mentions": [
        {
          "@id": "# Link to DOI or zenodo materials (10.5281/zenodo.7660225)",
          "@type": "Thing"
        },
        {
          "@id": "#Another link to DOI or zenodo materials (10.5281/zenodo.7565997)",
          "@type": "Thing"
        }
      ],
      "name": "# Name of the workshop (Introduction to bulk RNAseq analysis workshop)",
      "educationalLevel": "# One of: Beginner, Intermediate or Advanced",
      "audience": "# PhD, postdocs, MSc, etc"
    }
```

The example above includes the schema standard, `@context`, which is fixed. It also contains the link to the course, `@id`, and  specifies that it is a learning resource, `@type`. Additionally, you will find keywords, the type of learning resource, and a user license. The `mentions` item allows you to create multiple objects of `@type: Thing` with a link (`@id`). These could be datasets, slides, and other open material. Finally, you have a few other descriptors for the course.

For a more complete example, refer to the file `resources/bioschema_example.html` for inspiration. You can explore all the terms that can be used in a bioschema by looking at the [bioschemas for training material](https://bioschemas.org/profiles/TrainingMaterial/1.0-RELEASE). To verify your bioschema, you can either: a. Copy and paste the code from `bioschema.html`, b. Use the published webpage address (once it is published with the bioschema included in the configuration file) [here](https://validator.schema.org/). This will provide a report on the elements of the bioschema.

## Writing a webpage in `qmd` format

A standard webpage is in `qmd` format, which is essentially a markdown document with some metadata at the very beginning. This metadata contains information such as references, a date to display, and few other details. In addition to regular markdown syntax, you can also use admonitions and code blocks, which you can execute. The `index.qmd` webpage is a basic example that contains some elements.

## Adding Rmd files

`R markdown`, or abbreviated as `Rmd`, files can be used as webpages (as indicated by one of the menu items in the configuration file). However, these files need to be knitted and executed, so you need all the relevant R packages to be installed. Once processed, the `Rmd` file will become a visually nice-looking webpage, where you can also include bibliography references. Look at the example page `rmd/rmarkdown_example.Rmd` to better understand how things need to be coded.

## Adding Jupyter Notebooks

Files in `ipynb` format can similarly be used as webpages, with the advantage that they don't require compilation. They are read as-is and converted into a web format directly. Interactive plots, if present, should function properly on the webpage.

## Listing people

You can create pages containing lists (such as listing blog items or other lists). In our example, `people.qmd` has specific metadata dedicated to this purpose:

```yml
---
title: "People"
listing:
  contents: cards/*.qmd
  type: default
---
```

The webpage aims to display the people involved in the sandbox project. Each person is represented by a qmd file located in the cards folder, containing a picture, description, and some links. We specify the location of these items to be displayed using the `contents` option. 

## Push 'n Publish

If you want to see the webpage under development, you can simply run the command `quarto preview` from your command line while inside the folder with the configuration file.

The webpage can be published by simply pushing it on Github. There is a Github workflow in the folder `.github\workflows\publish.yml` which does all of that. Unfortunately, if you need additional `R` packages, then you have to change the workflow on your own. You can do this by taking a `snapshot` of the R you use for development (after loading all required packages). That should produce a file called `renv.lock` that you can use to substitute the one present in this repository. Read more on R environments [here](https://github.com/hds-sandbox/ucloud_development/blob/main/ucloud_develop_docs.md#rstudio-based-apps).

It can be very annoying trying to make the workflow work and testing it until it does. You can also deploy manually the webpage by:

* deleting the workflow file `.github\workflows\publish.yml` (which will otherwise always try to run)
* run `quarto publish gh-pages` on your command line
