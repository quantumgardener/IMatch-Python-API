import sys
import logging

import config
import flickr
import IMatchAPI as im
import pixelfed

logging.basicConfig(
    level = logging.INFO,
    format = '%(levelname)8s | %(message)s'
    )

class Factory():

    platforms = {
        'flickr' : {
            'image' : flickr.FlickrImage,
            'controller' : flickr.FlickrController,
        },
        'pixelfed' : {
            'image' : pixelfed.PixelfedImage,
            'controller' : pixelfed.PixelfedController
        }
    }

    def __init__(self) -> None:
        pass
        
    @classmethod
    def build_image(cls, id, platform): 
        try:
            print(cls.platforms[platform.name])
            return cls.platforms[platform.name]['image'](id, platform)
        except KeyError:
            print(f"{cls.__name__}.build(platform): '{platform.name}' is an unrecognised platform. Valid options are {cls.platforms.keys()}.")
            sys.exit()
        
    @classmethod
    def build_controller(cls, platform):
        try:
            return cls.platforms[platform]['controller'](platform)
        except KeyError:
            print(f"{cls.__name__}.build(platform): '{platform.name}' is an unrecognised platform. Valid options are {cls.platforms.keys()}.")
            sys.exit()
          
if __name__ == "__main__":

    if not sys.version_info >= (3, 10):
        print(f"Python version 3.10 or later required. You are running with version {sys.version_info.major}.{sys.version_info.minor}")
        sys.exit()


    # Retreive the complete list of Socials files from IMatch for all known
    # platforms. Within IMatch, files are in the Socials|{platform} category
    # or subcategories.

    ##pprint(IMatchAPI.get_imatch("v1/collections",params={'id' : 'all','fields':'id,path'}))
    
    images = []             # main image store
    platform_controllers = set()

    im.IMatchAPI()             # Perform initial connection
    
    # Gather all image information
    for platform in Factory.platforms.keys():
        platform_controllers.add(Factory.build_controller(platform))

    for controller in platform_controllers:
        logging.info( "--------------------------------------------------------------------------------------")
        logging.info(f"{controller.name}: Gathering images from IMatch.")
        for image_id in im.IMatchAPI.get_files_in_category(im.IMatchUtility.build_category([config.ROOT_CATEGORY,controller.name])):
            image = Factory.build_image(image_id, controller)
        logging.info(f"{controller.name}: {controller.stats['total']} images gathered from IMatch.")

        controller.classify_images()
        controller.add_images()
        controller.update_images()
        controller.delete_images()
        #controller.list_errors()
        controller.summarise()

    stats = {}
    for controller in platform_controllers:
        platform_stats = controller.stats
        for stat in platform_stats:
            try:
                stats[stat] += platform_stats[stat]
            except KeyError:
                stats[stat] = platform_stats[stat]
            
    logging.info( "--------------------------------------------------------------------------------------")
    logging.info(f"Final summary of images processed")
    for val in stats.keys():
        logging.info(f"-- {stats[val]} {val} images")
    
    logging.info("--------------------------------------------------------------------------------------")
    logging.info("Done.")


