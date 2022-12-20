import dotenv
from dotenv import load_dotenv
import asyncio
from playwright.async_api import async_playwright
import base64
import os
import pyotp


def getCode():
    userToken = os.getenv('TOKEN')
    count = int(os.getenv('COUNT'))
    dotenv.set_key(envPath, "COUNT", str(count + 1))

    encoded_secret = base64.b32encode(userToken.encode("utf-8"))

    return pyotp.HOTP(encoded_secret).at(count)


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(
            "https://mycourses.rit.edu/Shibboleth.sso/Login?entityID=https%3A%2F%2Fshibboleth.main.ad.rit.edu%2Fidp%2Fshibboleth&target=https%3A%2F%2Fmycourses.rit.edu%2Fd2l%2FshibbolethSSO%2Flogin.d2l%3Ftarget%3D%252Fd2l%252Fhome")

        username = os.getenv("USERNAME")
        password = os.getenv("PASSWORD")
        await page.get_by_placeholder("RIT Username").fill(username)
        await page.get_by_placeholder("Password").fill(password)
        await page.get_by_text("Login", exact=True).click()
        await page.get_by_text("Other options", exact=True).click()
        await page.get_by_text("Enter a code from the Duo Mobile app", exact=True).click()

        await page.get_by_label("Passcode").fill(str(getCode()))

        await page.get_by_role("button", name="Verify").click()

        await page.get_by_role("button", name="Yes, trust browser").click()

        storage = await context.storage_state(path="state.json")
        session_storage = await page.evaluate("() => JSON.stringify(sessionStorage)")
        dotenv.set_key(envPath, "SESSION_STORAGE", session_storage)

        await context.close()
        await browser.close()


envPath = "/Users/bobby/Documents/Projects/LoginScript/secrets.env"

load_dotenv(envPath)

asyncio.run(main())
