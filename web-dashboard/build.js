const esbuild = require('esbuild');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
const { promisify } = require('util');

const execAsync = promisify(exec);

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

// Build Tailwind CSS
async function buildTailwind() {
  try {
    console.log('🎨 Building Tailwind CSS...');
    const tailwindCommand = isProduction
      ? 'npx tailwindcss -i ./static/css/main.css -o ./static/css/output.css --minify'
      : 'npx tailwindcss -i ./static/css/main.css -o ./static/css/output.css';
    
    await execAsync(tailwindCommand);
    console.log('✅ Tailwind CSS build completed!');
  } catch (error) {
    console.error('❌ Tailwind CSS build failed:', error);
    throw error;
  }
}

// Build function
async function build() {
  try {
    // Clean output directory
    const outputDir = path.dirname(buildOptions.outfile);
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    // Build Tailwind CSS first
    await buildTailwind();

    if (isWatch) {
      // Watch mode
      console.log('👀 Starting watch mode...');
      
      // Watch Tailwind CSS
      const tailwindWatch = exec(
        'npx tailwindcss -i ./static/css/main.css -o ./static/css/output.css --watch',
        (error) => {
          if (error) {
            console.error('❌ Tailwind watch error:', error);
          }
        }
      );
      
      // Watch JavaScript
      const ctx = await esbuild.context(buildOptions);
      await ctx.watch();
      console.log('🚀 Build completed. Watching for changes...');
    } else {
      // Single build
      console.log('🔨 Building JavaScript...');
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