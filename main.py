import asyncio
from parser import ProductParser, ProductDetailParser, CSVExporter

if __name__ == '__main__':
    parser = ProductParser(
        base_url='https://berg-air.ru/catalog/vintovye-kompressory/',
        pagination_param='PAGEN_1',
        max_pages=2,
        card_selector='.catalog-section-item-content',
        title_selector='.catalog-section-item-name-wrapper',
        link_selector='a'
    )


    products = asyncio.run(parser.parse_all())

    detail_parser = ProductDetailParser(
        features_block_selector='.catalog-element-section-properties',
        param_name_selector='.catalog-element-section-property-name',
        param_value_selector='.catalog-element-section-property-value',
        price_selector='.catalog-element-price-discount',
        discount_price_selector='.catalog-element-offers-property-value-text-checkbox-price',
        image_selector='.catalog-element-gallery-picture-wrapper img'
    )

    detailed_products = asyncio.run(detail_parser.parse_all_product_details(products))

    exporter = CSVExporter('products.csv')
    exporter.export(detailed_products)
