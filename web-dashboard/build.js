const esbuild = require('esbuild');
const fs = require('fs');
const path = require('path');

// Parse command line arguments
const args = process.argv.slice(2);
const isWatch = args.includes('--watch');
const isProduction = args.includes('--production');

// Common build options
const buildOptions = {
  entryPoints: ['static/js/main.js'],
  bundle: true,
  outfile: 'static/js/bundle.js',
  platform: 'browser',
  target: ['es2020'],
  loader: {
    '.js': 'js',
    '.css': 'css'
  },
  minify: isProduction,
  sourcemap: !isProduction,
  define: {
    'process.env.NODE_ENV': isProduction ? '"production"' : '"development"'
  }
};

// Build function
async function build() {
  try {
    // Clean output directory
    const outputDir = path.dirname(buildOptions.outfile);
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    if (isWatch) {
      // Watch mode
      console.log('👀 Starting watch mode...');
      const ctx = await esbuild.context(buildOptions);
      await ctx.watch();
      console.log('🚀 Build completed. Watching for changes...');
    } else {
      // Single build
      console.log('🔨 Building...');
      await esbuild.build(buildOptions);
      console.log('✅ Build completed successfully!');
    }
  } catch (error) {
    console.error('❌ Build failed:', error);
    process.exit(1);
  }
}

// Run build
build();