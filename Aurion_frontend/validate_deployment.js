#!/usr/bin/env node
/**
 * Pre-Deployment Validation Script for AURION Frontend
 * Run this before deploying to catch common issues
 */

const fs = require('fs');
const path = require('path');

const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function checkFileExists(filepath, description) {
  if (fs.existsSync(filepath)) {
    log(`✅ ${description}: ${filepath}`, 'green');
    return true;
  } else {
    log(`❌ MISSING ${description}: ${filepath}`, 'red');
    return false;
  }
}

function checkEnvFile() {
  const envPath = path.join(__dirname, '.env');
  const envExamplePath = path.join(__dirname, '.env.example');
  
  if (!fs.existsSync(envExamplePath)) {
    log('❌ CRITICAL: .env.example file not found!', 'red');
    return false;
  }
  
  log('✅ .env.example exists', 'green');
  
  if (!fs.existsSync(envPath)) {
    log('⚠️  WARNING: .env file not found for local development', 'yellow');
    log('   This is OK if deploying to production', 'yellow');
    log('   For local dev, create .env from .env.example', 'yellow');
    return true; // Not critical for deployment
  }
  
  log('✅ .env file exists', 'green');
  
  // Check for required variables
  const envContent = fs.readFileSync(envPath, 'utf-8');
  const requiredVars = ['VITE_API_BASE_URL', 'VITE_BACKEND_URL'];
  
  const missing = requiredVars.filter(varName => {
    return !envContent.includes(`${varName}=`) || 
           envContent.includes(`${varName}=your`);
  });
  
  if (missing.length > 0) {
    log(`⚠️  WARNING: These variables might not be set: ${missing.join(', ')}`, 'yellow');
    return false;
  }
  
  log('✅ All critical environment variables appear to be set', 'green');
  return true;
}

function checkHardcodedUrls() {
  log('\n🔍 Checking for hardcoded URLs in source files...', 'blue');
  
  const srcDir = path.join(__dirname, 'src');
  const configFile = path.join(srcDir, 'config', 'env.ts');
  
  if (!fs.existsSync(configFile)) {
    log('❌ CRITICAL: src/config/env.ts not found!', 'red');
    log('   This file is required for environment configuration', 'red');
    return false;
  }
  
  log('✅ Environment configuration file exists', 'green');
  
  // Check if components use the ENV import
  const filesToCheck = [
    'src/react-app/components/AuthModal.tsx',
    'src/react-app/pages/ChatPage.tsx',
    'src/react-app/services/textSelectionService.ts',
    'src/react-app/services/adminApi.ts',
  ];
  
  let allGood = true;
  
  for (const file of filesToCheck) {
    const fullPath = path.join(__dirname, file);
    if (fs.existsSync(fullPath)) {
      const content = fs.readFileSync(fullPath, 'utf-8');
      
      // Check if file imports ENV
      if (!content.includes('from \'@/config/env\'') && 
          !content.includes('from "@/config/env"')) {
        log(`⚠️  ${file} doesn't import ENV config`, 'yellow');
        allGood = false;
      }
      
      // Check for hardcoded localhost
      if (content.includes('localhost') || content.includes('127.0.0.1')) {
        const lines = content.split('\n');
        lines.forEach((line, idx) => {
          if ((line.includes('localhost') || line.includes('127.0.0.1')) &&
              !line.trim().startsWith('//') &&
              !line.includes('import.meta.env')) {
            log(`⚠️  Found hardcoded URL in ${file}:${idx + 1}`, 'yellow');
            allGood = false;
          }
        });
      }
    }
  }
  
  if (allGood) {
    log('✅ No hardcoded URLs found in components', 'green');
  }
  
  return allGood;
}

function checkPackageJson() {
  log('\n📦 Checking package.json...', 'blue');
  
  const packagePath = path.join(__dirname, 'package.json');
  if (!fs.existsSync(packagePath)) {
    log('❌ CRITICAL: package.json not found!', 'red');
    return false;
  }
  
  const pkg = JSON.parse(fs.readFileSync(packagePath, 'utf-8'));
  
  // Check for required scripts
  const requiredScripts = ['build', 'dev'];
  const missingScripts = requiredScripts.filter(script => !pkg.scripts[script]);
  
  if (missingScripts.length > 0) {
    log(`❌ Missing required scripts: ${missingScripts.join(', ')}`, 'red');
    return false;
  }
  
  log('✅ package.json is properly configured', 'green');
  return true;
}

function checkVercelConfig() {
  log('\n🔧 Checking Vercel configuration...', 'blue');
  
  const vercelPath = path.join(__dirname, 'vercel.json');
  if (!fs.existsSync(vercelPath)) {
    log('❌ CRITICAL: vercel.json not found!', 'red');
    return false;
  }
  
  const config = JSON.parse(fs.readFileSync(vercelPath, 'utf-8'));
  
  if (!config.buildCommand) {
    log('⚠️  WARNING: buildCommand not specified in vercel.json', 'yellow');
  }
  
  if (!config.outputDirectory) {
    log('⚠️  WARNING: outputDirectory not specified in vercel.json', 'yellow');
  }
  
  log('✅ vercel.json exists', 'green');
  return true;
}

function main() {
  log('='.repeat(60), 'blue');
  log('AURION Frontend - Pre-Deployment Validation', 'blue');
  log('='.repeat(60), 'blue');
  console.log();
  
  let allGood = true;
  
  // Check critical files
  log('📋 Checking Critical Files...', 'blue');
  allGood &= checkFileExists('package.json', 'Package configuration');
  allGood &= checkFileExists('vercel.json', 'Vercel configuration');
  allGood &= checkFileExists('vite.config.ts', 'Vite configuration');
  allGood &= checkFileExists('src/config/env.ts', 'Environment config');
  allGood &= checkFileExists('.env.example', 'Environment template');
  console.log();
  
  // Check environment
  log('🔑 Checking Environment Configuration...', 'blue');
  allGood &= checkEnvFile();
  console.log();
  
  // Check for hardcoded URLs
  allGood &= checkHardcodedUrls();
  console.log();
  
  // Check package.json
  allGood &= checkPackageJson();
  console.log();
  
  // Check Vercel config
  allGood &= checkVercelConfig();
  console.log();
  
  // Final verdict
  log('='.repeat(60), 'blue');
  if (allGood) {
    log('✅ All checks passed! Ready for deployment', 'green');
    console.log();
    log('Next steps:', 'blue');
    log('1. Push code to GitHub', 'blue');
    log('2. Deploy on Vercel', 'blue');
    log('3. Add environment variables in Vercel dashboard', 'blue');
    return 0;
  } else {
    log('❌ Some issues found. Please fix them before deploying.', 'red');
    console.log();
    log('See documentation:', 'blue');
    log('- ENV_SETUP_GUIDE.md for environment setup', 'blue');
    log('- DEPLOYMENT_GUIDE.md for deployment steps', 'blue');
    return 1;
  }
}

process.exit(main());
