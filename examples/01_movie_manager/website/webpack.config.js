const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const path = require('path');

module.exports = {
  mode: process.env.NODE_ENV === 'production' ? 'production' : 'development',
  entry: './ts/main.ts',
  // Templates import from the bundle as an ES module,
  // import { X } from '{% static "main.js" %}', which needs module output.
  experiments: {
    outputModule: true,
  },
  devtool: process.env.NODE_ENV === 'production' ? false : 'source-map',
  output: {
    // The app's static/ folder, which Django's app directories finder serves.
    path: path.resolve(__dirname, 'static'),
    filename: 'main.js',
    // Lazily imported chunks are requested by webpack's runtime at the URL it
    // computes from import.meta.url, so a versioning static storage such as
    // ManifestStaticFilesStorage never gets a chance to rewrite them to their
    // hashed names. A server that caches /static/ for a long time would keep
    // serving returning visitors a stale chunk, so the content hash has to be
    // baked into the filename here.
    chunkFilename: 'chunks/[name].[contenthash].js',
    // Chunks are confined to chunks/ so stale ones from previous builds can be
    // removed without touching other files in static/, such as images.
    clean: {
      keep: (asset) => !asset.startsWith('chunks/'),
    },
    library: {
      type: 'module',
    },
  },
  resolve: {
    extensions: ['.ts', '.js'],
  },
  module: {
    rules: [
      {
        test: /\.ts$/,
        use: 'ts-loader',
      },
      {
        test: /\.scss$/,
        use: [
          MiniCssExtractPlugin.loader,
          'css-loader',
          'sass-loader',
        ],
      },
      {
        test: /\.css$/,
        use: [
          MiniCssExtractPlugin.loader,
          'css-loader',
        ],
      },
    ],
  },
  plugins: [
    // Every stylesheet main.ts imports, as one file, which the document
    // template links.
    new MiniCssExtractPlugin({
      filename: 'bundled-styles.css',
    }),
  ],
};
