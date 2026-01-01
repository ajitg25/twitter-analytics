/**
 * Twitter Cookie Extractor using Playwright
 * 
 * Two modes:
 * 1. Uses your existing Chrome profile (if already logged in)
 * 2. Fresh login with Playwright browser
 * 
 * Usage: node extract-cookies.js
 */

import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import os from 'os';
import readline from 'readline';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Find Chrome user data directory
function getChromeUserDataDir() {
    const platform = os.platform();
    const home = os.homedir();
    
    if (platform === 'darwin') {
        return path.join(home, 'Library', 'Application Support', 'Google', 'Chrome');
    } else if (platform === 'win32') {
        return path.join(home, 'AppData', 'Local', 'Google', 'Chrome', 'User Data');
    } else {
        return path.join(home, '.config', 'google-chrome');
    }
}

async function waitForEnter() {
    const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout
    });
    
    return new Promise(resolve => {
        rl.question('', () => {
            rl.close();
            resolve();
        });
    });
}

async function extractWithPersistentProfile() {
    console.log('\n📂 Mode: Using persistent browser profile');
    console.log('   This creates a new profile that persists between runs.\n');
    
    const userDataDir = path.join(__dirname, '.playwright-profile');
    
    const context = await chromium.launchPersistentContext(userDataDir, {
        headless: false,
        viewport: { width: 1280, height: 800 },
        userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        args: [
            '--disable-blink-features=AutomationControlled'
        ]
    });
    
    const page = context.pages()[0] || await context.newPage();
    
    // Open Twitter/X
    console.log('🌐 Opening Twitter/X...');
    await page.goto('https://x.com/home', { waitUntil: 'domcontentloaded', timeout: 120000 });
    
    // Wait a moment for cookies to load
    await page.waitForTimeout(3000);
    
    // Check for auth cookies from both twitter.com and x.com (after rebrand)
    let cookies = await context.cookies();  // Get ALL cookies
    let authToken = cookies.find(c => c.name === 'auth_token');
    
    if (!authToken) {
        console.log('\n⚠️  Not logged in. Please log in manually in the browser window.');
        console.log('   (Handle 2FA, captcha, etc. as needed)\n');
        console.log('   👉 After you see your Twitter feed, wait 5 seconds, then press ENTER here...\n');
        await waitForEnter();
        
        console.log('🔄 Capturing cookies...');
        
        // Navigate to x.com (Twitter's new domain) to ensure cookies are set
        await page.goto('https://x.com/home', { waitUntil: 'domcontentloaded', timeout: 30000 });
        
        // Wait for cookies to fully propagate
        await page.waitForTimeout(5000);
        
        // Re-fetch ALL cookies (from all domains)
        cookies = await context.cookies();
        
        // Show unique cookie names
        const uniqueNames = [...new Set(cookies.map(c => c.name))];
        console.log('📋 Found cookies:', uniqueNames.join(', '));
        
        // Also show domains for debugging
        const domains = [...new Set(cookies.map(c => c.domain))];
        console.log('🌐 From domains:', domains.join(', '));
    } else {
        console.log('✅ Already logged in!');
    }
    
    await context.close();
    
    return cookies;
}

async function extractWithFreshBrowser() {
    console.log('\n🆕 Mode: Fresh browser (login required)');
    
    const browser = await chromium.launch({
        headless: false,
        args: [
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox'
        ]
    });
    
    const context = await browser.newContext({
        viewport: { width: 1280, height: 800 },
        userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        locale: 'en-US',
        timezoneId: 'America/New_York'
    });
    
    const page = await context.newPage();
    
    // Navigate to Twitter/X
    console.log('🌐 Opening Twitter/X login...');
    await page.goto('https://x.com/i/flow/login', { waitUntil: 'domcontentloaded', timeout: 120000 });
    
    console.log('\n📌 Please log in manually in the browser window.');
    console.log('   (Handle 2FA, captcha, etc. as needed)\n');
    console.log('   👉 After you see your feed, wait 5 seconds, then press ENTER here...\n');
    
    await waitForEnter();
    
    // Wait for cookies
    await page.waitForTimeout(3000);
    
    // Extract ALL cookies
    const cookies = await context.cookies();
    await browser.close();
    
    return cookies;
}

async function main() {
    console.log('🐦 Twitter Cookie Extractor (Playwright)');
    console.log('=========================================\n');
    
    // Check for --fresh flag to use fresh browser instead
    const useFreshBrowser = process.argv.includes('--fresh');
    
    let cookies;
    
    if (useFreshBrowser) {
        cookies = await extractWithFreshBrowser();
    } else {
        // Default: Use persistent profile (recommended)
        cookies = await extractWithPersistentProfile();
    }
    
    // Find the important cookies
    const authToken = cookies.find(c => c.name === 'auth_token');
    const ct0 = cookies.find(c => c.name === 'ct0');
    
    if (!authToken || !ct0) {
        console.log('\n❌ Could not find required cookies.');
        console.log('   Make sure you are fully logged in to Twitter.\n');
        console.log('   Found cookies:', cookies.map(c => c.name).join(', '));
        process.exit(1);
    }
    
    // Format the API key
    const apiKey = `${authToken.value};${ct0.value}`;
    
    console.log('\n✅ Cookies extracted successfully!');
    console.log('\n📋 Your API Key (first 50 chars):');
    console.log('─'.repeat(60));
    console.log(apiKey.substring(0, 50) + '...');
    console.log('─'.repeat(60));
    
    // Update .env file
    const envPath = path.join(__dirname, '..', '.env');
    
    try {
        let envContent = '';
        if (fs.existsSync(envPath)) {
            envContent = fs.readFileSync(envPath, 'utf8');
        }
        
        // Update or add RETTIWT_API_KEY
        if (envContent.includes('RETTIWT_API_KEY=')) {
            envContent = envContent.replace(
                /RETTIWT_API_KEY=.*/,
                `RETTIWT_API_KEY=${apiKey}`
            );
        } else {
            envContent += `\nRETTIWT_API_KEY=${apiKey}\n`;
        }
        
        fs.writeFileSync(envPath, envContent);
        console.log('\n✅ Updated .env file with new API key');
        
    } catch (err) {
        console.log('\n⚠️  Could not update .env automatically.');
        console.log('   Add this to your .env:');
        console.log(`   RETTIWT_API_KEY=${apiKey}`);
    }
    
    console.log('\n🚀 Next steps:');
    console.log('   1. Restart service: npm start');
    console.log('   2. Test: curl http://localhost:3001/api/user/Twitter');
    console.log('\n💡 Tip: Run "npm run auth" again anytime - your login persists!');
    console.log('   Use "npm run auth:fresh" for a new browser session.');
}

main().catch(err => {
    console.error('Error:', err.message);
    process.exit(1);
});
