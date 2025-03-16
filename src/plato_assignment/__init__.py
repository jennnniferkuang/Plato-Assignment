import asyncio
# import requests
# from bs4 import BeautifulSoup
from scrapybara import Scrapybara
from undetected_playwright.async_api import async_playwright

async def get_scrapybara_browser():
    client = Scrapybara(api_key="scrapy-a9439aae-0904-4dfe-98f7-b75b75b88e8a")
    instance = client.start_browser()
    return instance

async def retrieve_menu_items(instance, start_url: str) -> list[dict]:
    """
    :args:
    instance: the scrapybara instance to use
    url: the initial url to navigate to

    :desc:
    this function navigates to {url}. then, it will collect the detailed
    data for each menu item in the store and return it.

    (hint: click a menu item, open dev tools -> network tab -> filter for
            "https://www.doordash.com/graphql/itemPage?operation=itemPage")

    one way to do this is to scroll through the page and click on each menu
    item.

    determine the most efficient way to collect this data.

    :returns:
    a list of menu items on the page, represented as dictionaries
    """
    cdp_url = instance.get_cdp_url().cdp_url
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(cdp_url)
        page = await browser.new_page()

        await page.goto(start_url)

        # browser automation ...

        # html_content = await page.content()
        # print(html_content)

        await page.wait_for_load_state("networkidle")  # Ensure content loads
        # Scroll to load all menu items
        previous_height = 0
        while True:
            await page.evaluate("window.scrollBy(0, 1000)")  # Scroll down
            await asyncio.sleep(1)  # Allow time for items to load
            new_height = await page.evaluate("document.body.scrollHeight")

            if new_height == previous_height:  # Stop when no more new content loads
                break
            previous_height = new_height

        # Find all menu item tiles using data-anchor-id
        sections = await page.query_selector_all('[data-testid="VirtualGridContainer"]')
        # print(sections)
        # print(f"Found {len(sections)} menu sections.")  # Debugging step
        
        menu_data = {}
        for container in sections:
            await container.scroll_into_view_if_needed()  # Scroll to make section visible
            await asyncio.sleep(1)  # Wait for new items to load
            # inner_html = await container.inner_html()
            # print(inner_html)
            menu_items = await container.query_selector_all('[data-anchor-id="MenuItem"]')
            #data-anchor-id="MenuItem"

            for item in menu_items:
                name = await item.query_selector('[data-telemetry-id="storeMenuItem.title"]')
                nameStr = await name.inner_html()
                try:
                    subtitle = await item.query_selector('[data-telemetry-id="storeMenuItem.subtitle"]')
                    subtitleStr = await subtitle.inner_html()
                except:
                    subtitleStr = ''
                try:
                    price = await item.query_selector('[data-anchor-id="StoreMenuItemPrice"]')
                    priceStr = await price.inner_html()
                except:
                    priceStr = ''
                menu_data[nameStr] = {'description': subtitleStr, 'price': priceStr}
            # menu_items += add_items
            # print(f"Found {len(menu_items)} menu items.")  # Debugging step
        print(menu_data)
        return menu_data
        # data-telemetry-id="storeMenuItem.title"


        # html_content = await page.content()
        # # await page.wait_for_selector('[role="button"]', timeout=5000)
        # # menu_items = await page.query_selector_all('[class="ModalFrame__ModalFrameMain-sc-19okh4j-1 bZuMPX"]')
        # # print(page.content)
        # soup = BeautifulSoup(html_content, 'html.parser')
        # print(soup.find_all('div', "data-anchor-id='MenuItem'"))
        # #menu_items = soup.find_all("div", {"class": "ModalFrame__ModalFrameMain-sc-19okh4j-1 bZuMPX"})
        # #print(menu_items)
        
        # #data-testid="GenericItemCard"
        # #data-testid="MenuItem"
        
# async def retrieve_menu_items(instance, start_url: str) -> list[dict]:
#     """
#     Navigates to the restaurant menu page, clicks on each item, and extracts item details.

#     :param instance: The Scrapybara instance.
#     :param start_url: The URL of the restaurant page.
#     :return: A list of dictionaries containing menu item data.
#     """
#     cdp_url = instance.get_cdp_url().cdp_url
#     async with async_playwright() as p:
#         browser = await p.chromium.connect_over_cdp(cdp_url)
#         page = await browser.new_page()
#         await page.goto(start_url)

#         # Store extracted menu data
#         menu_data = []

#         # Function to capture GraphQL API response
#         async def intercept_response(response):
#             if "graphql/itemPage?operation=itemPage" in response.url:
#                 json_data = await response.json()
#                 menu_data.append(json_data)

#         # Attach network interception
#         page.on("response", intercept_response)

#         # Find all menu items
#         menu_items = await page.query_selector_all('[role="button"]')

#         # Click each menu item to trigger API request
#         for item in menu_items:
#             await item.click()
#             # await page.wait_for_timeout(1000)  # Small delay

#         print(menu_data)
#         return menu_data  # Return extracted details



async def main():
    instance = await get_scrapybara_browser()
    print("running...")

    try:
        await retrieve_menu_items(
            instance,
            "https://www.doordash.com/store/panda-express-san-francisco-980938/12722988/?event_type=autocomplete&pickup=false",
        )
        # "https://www.doordash.com/store/panda-express-san-francisco-980938/12722988/?event_type=autocomplete&pickup=false"
    finally:
        # Be sure to close the browser instance after you're done!
        instance.stop()
        # pass


if __name__ == "__main__":
    asyncio.run(main())
