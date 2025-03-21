import asyncio
# import requests
# from bs4 import BeautifulSoup
from scrapybara import Scrapybara
from undetected_playwright.async_api import async_playwright

async def get_scrapybara_browser():
    client = Scrapybara(api_key="scrapy-key")
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
            await asyncio.sleep(0.5)  # Allow time for items to load
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
            await asyncio.sleep(0.5)  # Wait for new items to load
            # inner_html = await container.inner_html()
            # print(inner_html)
            menu_items = await container.query_selector_all('[data-anchor-id="MenuItem"]')
            #data-anchor-id="MenuItem"

            for item in menu_items:

                # scrape basic info from tile (name, subtitle)
                name = await item.query_selector('[data-telemetry-id="storeMenuItem.title"]')
                nameStr = await name.inner_text()
                try:
                    subtitle = await item.query_selector('[data-telemetry-id="storeMenuItem.subtitle"]')
                    subtitleStr = await subtitle.inner_text()
                except:
                    subtitleStr = ''
                
                # open pop-up
                try:
                    await item.click()
                    await asyncio.sleep(1)

                    popup = await page.query_selector('[data-testid="itemBody"]')

                    print('opened popup')

                    option_lists = await popup.query_selector_all('[aria-labelledby^="optionList_"]')
                    print(f"Found {len(option_lists)} options in {nameStr}")

                    print('found option list')

                    for list in option_lists:
                        try:
                            options = await list.query_selector_all('[class^="styles__ToggleContainer"]')
                            # option_name = await list.query_selector('[h3]')
                            try:
                                option_name = (await list.get_attribute('[aria-labelledby]')) #.rpartition('_')[2]
                            except:
                                option_name = 'label not found'
                            print(option_name)
                            list_items = []
                            for i in range (len(options)):
                                list_items.append((await options[i].inner_text()).split('\n')[0])
                            print(list_items)
                            menu_data[nameStr][option_name] = list_items
                        except:
                            print('no contents found')
                    
                    # print(menu_data)
                    await page.keyboard.press("Escape")
                
                # if the item does not open, just scrape data from item tile
                except:
                    try:
                        price = await item.query_selector('[data-anchor-id="StoreMenuItemPrice"]')
                        priceStr = await price.inner_html()
                    except:
                        priceStr = ''
                    menu_data[nameStr] = {'description': subtitleStr, 'price': priceStr}
                    print("unable to open popup.")

        # print(menu_data)
        return menu_data


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
