import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'openmem',
  tagline: 'Deterministic memory engine for AI agents',
  favicon: 'img/carrot.svg',

  future: {
    v4: true,
  },

  url: 'https://dunkinfrunkin.github.io',
  baseUrl: '/OpenMem/',

  organizationName: 'dunkinfrunkin',
  projectName: 'OpenMem',

  onBrokenLinks: 'throw',

  markdown: {
    mermaid: true,
  },

  themes: ['@docusaurus/theme-mermaid'],

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          editUrl: 'https://github.com/dunkinfrunkin/OpenMem/tree/main/web/',
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    colorMode: {
      respectPrefersColorScheme: true,
    },
    navbar: {
      title: 'openmem',
      logo: {
        alt: 'openmem',
        src: 'img/carrot.svg',
        width: 28,
        height: 28,
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'docsSidebar',
          position: 'left',
          label: 'Docs',
        },
        {
          href: 'https://github.com/dunkinfrunkin/OpenMem',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Docs',
          items: [
            {label: 'Quick Start', to: '/docs/quickstart'},
            {label: 'Claude Code', to: '/docs/claude-code'},
            {label: 'Web UI', to: '/docs/web-ui'},
            {label: 'API Reference', to: '/docs/api'},
          ],
        },
        {
          title: 'More',
          items: [
            {label: 'GitHub', href: 'https://github.com/dunkinfrunkin/OpenMem'},
          ],
        },
      ],
      copyright: `Copyright ${new Date().getFullYear()} OpenMem contributors. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['bash', 'python'],
    },
    mermaid: {
      theme: {light: 'neutral', dark: 'dark'},
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
