import os
import unittest
import time
import json


from appium import webdriver
from appium.webdriver.common.mobileby import MobileBy
from selenium.common.exceptions import NoSuchElementException


def write_to_file(data, hotel_name) -> None:
    with open(f'{hotel_name}.json', 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)


class TestTripAdvisorApp(unittest.TestCase):

    def setUp(self):
        self.hotel_name = "The Grosvenor Hotel"

        device = {
            "deviceName": "Tab_7",
            "platformName": "Android",
            "platformVersion": "11.0",
            "automationName": "UiAutomator2",
            "appActivity": "com.tripadvisor.android.ui.launcher.LauncherActivity",
            "appPackage": "com.tripadvisor.tripadvisor"
        }
        self.driver = webdriver.Remote("http://localhost:4723/wd/hub", device)
        self.driver.implicitly_wait(10)

    def tearDown(self):
        self.driver.quit()

    def test_skip_initial_screens(self):

        skip_btn = self.driver.find_element(
            MobileBy.ID,
            "com.tripadvisor.tripadvisor:id/bdlBtnSkip"
        )
        self.assertNotEqual(skip_btn, NoSuchElementException)
        skip_btn.click()

        not_now_btn = self.driver.find_element(
            MobileBy.ID,
            "com.tripadvisor.tripadvisor:id/bdlBtnNotNow"
        )
        self.assertNotEqual(not_now_btn, NoSuchElementException)
        not_now_btn.click()

    def test_search_hotel_and_extract_deals(self):
        self.test_skip_initial_screens()

        self.driver.find_element(
            MobileBy.ID,
            "com.tripadvisor.tripadvisor:id/chip"
        ).click()

        search_input = self.driver.find_element(
            MobileBy.ID,
            "com.tripadvisor.tripadvisor:id/edtSearchString"
        )
        search_input.click()
        search_input.send_keys(self.hotel_name)

        list_hotels = self.driver.find_elements(
            MobileBy.ID,
            "com.tripadvisor.tripadvisor:id/typeaheadResult"
        )

        found_hotel = False
        for hotel in list_hotels:
            hotel_name = hotel.find_element(
                MobileBy.ID,
                "com.tripadvisor.tripadvisor:id/txtHeading"
            )
            if hotel_name.text == self.hotel_name:
                hotel_name.click()
                found_hotel = True
                break

        self.assertTrue(
            found_hotel,
            f"The {self.hotel_name} not found in search results."
        )

        self.driver.find_element(
            MobileBy.ID,
            "com.tripadvisor.tripadvisor:id/txtDate"
        ).click()

        days = self.driver.find_elements(
            MobileBy.ID, "com.tripadvisor.tripadvisor:id/txtDay"
        )

        data = self.process_days(days)

        self.assertTrue(data, "No hotel deals were extracted.")

        write_to_file(data, self.hotel_name)

    def write_all_deals(
            self,
            proposals: list[webdriver],
    ) -> dict:

        date = self.driver.find_element(
            MobileBy.ID, "com.tripadvisor.tripadvisor:id/txtDate"
        ).text

        deal_name = proposals[0].find_element(
            MobileBy.ID, "com.tripadvisor.tripadvisor:id/imgProviderLogo"
        )
        deal_name = deal_name.get_attribute("content-desc")

        deal_price = proposals[0].find_element(
            MobileBy.ID, "com.tripadvisor.tripadvisor:id/txtPriceTopDeal"
        ).text

        screenshots_folder = os.path.join("screenshots", self.hotel_name)
        if not os.path.exists(screenshots_folder):
            os.makedirs(screenshots_folder)
        screenshot_path = os.path.join(
            screenshots_folder, f"{self.hotel_name}: {date}.png"
        )
        self.driver.save_screenshot(screenshot_path)

        hotels = {date: {deal_name: deal_price}}

        for proposal in proposals[1:]:
            try:
                name = proposal.find_element(
                    MobileBy.ID,
                    "com.tripadvisor.tripadvisor:id/txtProviderName"
                ).text

                price = proposal.find_element(
                    MobileBy.ID,
                    "com.tripadvisor.tripadvisor:id/txtPriceTopDeal"
                ).text

                hotels[date].update({name: price})
            except NoSuchElementException:
                continue

        hotels[date]["screenshot"] = screenshot_path
        return hotels

    def process_days(self, days: list[webdriver]) -> dict:
        hotel_json = {self.hotel_name: {}}

        for i in range(len(days)):
            all_days = self.driver.find_elements(
                MobileBy.ID, "com.tripadvisor.tripadvisor:id/dayView"
            )
            day = all_days[i]

            if day.get_attribute("clickable") == "true":
                day.click()
                self.driver.find_element(
                    MobileBy.ID,
                    "com.tripadvisor.tripadvisor:id/btnPrimary"
                ).click()
                try:
                    time.sleep(3)
                    self.driver.find_element(
                        MobileBy.ID,
                        "com.tripadvisor.tripadvisor:id/btnAllDeals"
                    ).click()

                    hotel_json[self.hotel_name].update(
                        self.write_all_deals(
                            self.driver.find_elements(
                                MobileBy.ID,
                                "com.tripadvisor.tripadvisor:id/cardHotelOffer"
                            ),
                        )
                    )

                    if len(hotel_json[self.hotel_name]) == 5:
                        return hotel_json

                    self.driver.back()

                    self.driver.find_element(
                        MobileBy.ID, "com.tripadvisor.tripadvisor:id/txtDate"
                    ).click()
                    self.driver.implicitly_wait(3)
                except NoSuchElementException:
                    self.driver.find_element(
                        MobileBy.ID, "com.tripadvisor.tripadvisor:id/txtDate"
                    ).click()
                    self.driver.implicitly_wait(3)
                    continue

        return hotel_json


if __name__ == "__main__":
    unittest.main()
