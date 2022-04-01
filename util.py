from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

#UTILITY METHOD FOR CLICKING ELEMENTS AS THERE ARE POSSIBILITES OF OTHER ELEMENTS OBSCURING THE INTENDED ELEMENT.
def click(driver,element):
    try:
        cancel=driver.find_element(by=By.ID,value="wzrk-cancel")
        cancel.click()
    except NoSuchElementException:
        pass
    finally:
        element.click()

