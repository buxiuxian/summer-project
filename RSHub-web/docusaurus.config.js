// @ts-check
// `@type` JSDoc annotations allow editor autocompletion and type checking
// (when paired with `@ts-check`).
// There are various equivalent ways to declare your Docusaurus config.
// See: https://docusaurus.io/docs/api/docusaurus-config

import {themes as prismThemes} from 'prism-react-renderer';

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'Remote Sensing Hub',
  tagline: 'Remote Sensing Hub is a shared cloud computing platform for the remote sensing community to compute microwave scattering',
  //favicon: 'img/favicon.ico',

  // Set the production url of your site here
  url: 'https://your-docusaurus-site.example.com',
  // Set the /<baseUrl>/ pathname under which your site is served
  // For GitHub pages deployment, it is often '/<projectName>/'
  baseUrl: '/',

  // GitHub pages deployment config.
  // If you aren't using GitHub pages, you don't need these.
  organizationName: 'ZJUI', // Usually your GitHub org/user name.
  projectName: 'RShub', // Usually your repo name.

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',

  // Even if you don't use internationalization, you can use this field to set
  // useful metadata like html lang. For example, if your site is Chinese, you
  // may want to replace "en" with "zh-Hans".
  i18n: {
    defaultLocale: 'en',
    locales: ['en', 'zh-Hans'],
    localeConfigs: {
      en: {
        htmlLang: 'en-US',
      },
      'zh-Hans': {
        htmlLang: 'zh-CN',
      },
    },
  },

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: './sidebars.js',
          // Please change this to your repo.
        },
        blog: {
          showReadingTime: true,
          // Please change this to your repo.
          // Remove this to remove the "edit this page" links.
        },
        theme: {
          customCss: './src/css/custom.css',
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      // Replace with your project's social card
      //image: 'img/docusaurus-social-card.jpg',
      navbar: {
        title: 'Remote Sensing Hub',
        logo: {
          alt: 'RSHub Logo',
          src: 'img/rshub.png',
          href: '/',
        },
        items: [
          {
            to: '/Getting-Started',
            position: 'left',
            label: 'Getting Started',
          },
          {
            type: 'doc',
            docId: 'Scenarios',
            label: 'Scenarios', 
            position: 'left'
          },
          {
            to: '/Acknowledgements', 
            label: 'Acknowledgements', 
            position: 'left'
          },
          {
            to: '/Agent',
            position: 'left',
            label: 'Agent',
            className: 'navbar-agent-link'
          },
          {
            type: 'localeDropdown',
            position: 'right'
          },
          {
            type: 'custom-NavbarLoginItem',
            position: 'right',
          },
        ],
        hideOnScroll: false,
      },
      
      prism: {
        theme: prismThemes.github,
        darkTheme: prismThemes.dracula,
      },
    }),
};

export default config;
