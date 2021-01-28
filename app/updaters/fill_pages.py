from .base_updater import RowsUpdater


class FillPageRowsUpdater(RowsUpdater):
    def iter_update(self):
        pass

    @staticmethod
    def save_products_batch(country: CountryCode, products: list):
        model = ProductsParser.get_model(country)
        model.insert_many(products).on_conflict(
            conflict_target=[model.code],
            update={
                model.data: EXCLUDED.data,
                model.is_failed: EXCLUDED.is_failed,
                model.loaded: EXCLUDED.loaded,
                model.is_translated: EXCLUDED.is_translated,
            }
        ).execute()


    def fill_products_generator(self, country: CountryCode, batch_size):
        """Get from db not loaded items. Parse pages and fill this lines in db"""
        while True:
            items = list(self.get_items_to_load(country, limit=batch_size))
            products = []
            for item in items:
                product = {
                    **item,
                    'loaded': True,
                    'is_translated': False,
                    'is_failed': False
                }
                try:
                    product.update(self.parse_product(country, item))
                except:
                    product.update({
                        'is_failed': True
                    })

                products.append(product)
            self.save_products_batch(country, products)
            yield len(items)
            if not items:
                return

    @log_on_error(logging.ERROR, 'Error filling products {country}', logger=logger)
    @log_on_end(logging.INFO, 'All products filled {country}', logger=logger)
    def fill_products(self, country: CountryCode):
        cut_products_count = self.session.query(IkeaProduct).filter(IkeaProduct.loaded == False).count()
        batch_size = 5
        logger.info('items_to_load_count %s', cut_products_count)
        for i in tqdm(self.fill_products_generator(country, batch_size), total=cut_products_count / batch_size):
            pass

    def get_items_to_load(self, country: CountryCode, limit: int = 10):
        items = self.session.query(IkeaProduct.code, IkeaProduct.url).filter(IkeaProduct.loaded == False, IkeaProduct.is_failed == False).limit(
            limit).dicts()
        return items

    @staticmethod
    def parse_product(cut_product) -> dict:
        data, tags = ParserUtils.parse_ikea_page(cut_product['url'])
        item = cut_product
        item['data'] = data
        item['tags'] = tags
        return item