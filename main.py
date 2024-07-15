import shutil

from bdffont import BdfFont
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables.E_B_D_T_ import ebdt_bitmap_format_5, ebdt_bitmap_format_7
from fontTools.ttLib.tables.E_B_L_C_ import Strike
from pixel_font_builder import FontBuilder, Glyph

from path_define import fonts_dir, build_dir


def main():
    outputs_dir = build_dir.joinpath('outputs')
    if outputs_dir.exists():
        shutil.rmtree(outputs_dir)
    outputs_dir.mkdir(parents=True)

    # 需要转换的目标字体
    tt_font = TTFont(fonts_dir.joinpath('Zfull-GB.ttf'))

    builder = FontBuilder()
    builder.font_metric.font_size = 12
    builder.font_metric.horizontal_layout.ascent = 11
    builder.font_metric.horizontal_layout.descent = -1
    builder.font_metric.vertical_layout.ascent = 6
    builder.font_metric.vertical_layout.descent = -6

    builder.meta_info.version = '1.0.0'
    builder.meta_info.family_name = 'Zfull GB'

    # 点阵数据遍历 ebdt 和 eblc 表
    # 格式参考：https://learn.microsoft.com/en-us/typography/opentype/spec/ebdt

    # format_5 中位对其度量是重用的
    metrics_bit_aligned = {}
    strike: Strike = tt_font['EBLC'].strikes[4]  # 取字形列表 4，应该是 11*11 的点阵
    for index_sub_table in strike.indexSubTables:
        if index_sub_table.imageFormat == 5:
            for glyph_name in index_sub_table.names:
                metrics_bit_aligned[glyph_name] = index_sub_table.metrics

    # 遍历 EBDT 表
    strike_data: dict[str, ebdt_bitmap_format_5 | ebdt_bitmap_format_7] = tt_font['EBDT'].strikeData[4]  # 取字形列表 4，同上
    for glyph_name, bitmap_data in strike_data.items():
        if isinstance(bitmap_data, ebdt_bitmap_format_5):
            # format_5 度量在上面重用池中
            metrics = metrics_bit_aligned[glyph_name]
        elif isinstance(bitmap_data, ebdt_bitmap_format_7):
            # format_7 的度量是内嵌的
            metrics = bitmap_data.metrics
        else:
            # 其他格式暂时未遇到，忽略
            raise RuntimeError(f"字形 '{glyph_name}' 的 bitmap_data 格式需要适配")

        # 获取度量
        width = metrics.width
        height = metrics.height
        hori_bearing_x = metrics.horiBearingX
        hori_bearing_y = metrics.horiBearingY
        hori_advance = metrics.horiAdvance
        vert_bearing_x = metrics.vertBearingX
        vert_bearing_y = metrics.vertBearingY
        vert_advance = metrics.vertAdvance

        # 位图的二进制字符串
        bitmap_string = ''
        for b in bitmap_data.imageData:
            bitmap_string += f'{b:08b}'

        # 根据宽高还原出单色位图
        bitmap = []
        for y in range(height):
            bitmap_row = []
            for x in range(width):
                bitmap_row.append(int(bitmap_string[width * y + x]))
            bitmap.append(bitmap_row)

        # 根据上述信息构建字形
        # 坐标系转换参考: https://freetype.org/freetype2/docs/glyphs/glyphs-3.html#section-3
        # 位图左下角在 Opentype 水平坐标系中的位置
        # 位图顶部中央在 Opentype 垂直坐标系中的位置
        builder.glyphs.append(Glyph(
            name=glyph_name,
            horizontal_origin=(hori_bearing_x, hori_bearing_y - height),
            advance_width=hori_advance,
            vertical_origin_y=vert_bearing_y,
            advance_height=vert_advance,
            bitmap=bitmap,
        ))

    # cmap 格式相同，直接使用
    # 但存在字形缺失的情况，这里手动移除
    glyph_names = set(glyph.name for glyph in builder.glyphs)
    for code_point, glyph_name in tt_font.getBestCmap().items():
        if glyph_name not in glyph_names:
            print(f'缺失字形：{glyph_name}')
            continue
        builder.character_mapping[code_point] = glyph_name

    # 写入到本地保存
    builder.save_bdf(outputs_dir.joinpath('zfull-gb.bdf'))
    builder.save_pcf(outputs_dir.joinpath('zfull-gb.pcf'))

    # 验证一下生成的字体
    # 加载 bdf 字体，然后打印出字形
    bdf_font = BdfFont.load(outputs_dir.joinpath('zfull-gb.bdf'))
    for glyph in bdf_font.glyphs:
        print(f'char: {chr(glyph.encoding)} ({glyph.encoding:04X})')
        print(f'glyph_name: {glyph.name}')
        print(f'advance_width: {glyph.device_width_x}')
        print(f'dimensions: {glyph.dimensions}')
        print(f'origin: {glyph.origin}')
        for bitmap_row in glyph.bitmap:
            text = ''.join('  ' if alpha == 0 else '██' for alpha in bitmap_row)
            print(f'{text}*')
        print()


if __name__ == '__main__':
    main()
