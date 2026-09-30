/*
   Copyright (c) 2015-2023 hkrn All rights reserved

   This file is part of emapp component and it's licensed under Mozilla Public License. see LICENSE.md for more details.
 */

#include "emapp/ModelNameDictionary.h"

#include "emapp/Error.h"
#include "emapp/FileUtils.h"
#include "emapp/StringUtils.h"
#include "emapp/URI.h"

namespace nanoem {

namespace {

/* 内置标准词典：MMD 标准骨骼 / 常用表情变形 / 常见材质的日译中对照表（TSV：日文名<TAB>中文名）。
   覆盖不到的名称回退原文；可执行文件同目录的 model_names_user.tsv 可补充或覆盖词条。 */
const char kBuiltInDictionary[] =
    "# standard bones\n"
    "全ての親\t全亲\n"
    "操作中心\t操作中心\n"
    "センター\t中心\n"
    "グルーブ\t律动\n"
    "腰\t腰\n"
    "腰キャンセル\t腰取消\n"
    "上半身\t上半身\n"
    "上半身2\t上半身2\n"
    "下半身\t下半身\n"
    "首\t颈\n"
    "頭\t头\n"
    "あご\t下巴\n"
    "顎\t下巴\n"
    "両目\t双眼\n"
    "右目\t右眼\n"
    "左目\t左眼\n"
    "右手\t右手\n"
    "左手\t左手\n"
    "右腕\t右臂\n"
    "左腕\t左臂\n"
    "右肩\t右肩\n"
    "左肩\t左肩\n"
    "右肩P\t右肩P\n"
    "左肩P\t左肩P\n"
    "右腕捩\t右臂扭\n"
    "左腕捩\t左臂扭\n"
    "右腕捩2\t右臂扭2\n"
    "左腕捩2\t左臂扭2\n"
    "右ひじ\t右肘\n"
    "左ひじ\t左肘\n"
    "右手首\t右手腕\n"
    "左手首\t左手腕\n"
    "右手捩\t右手扭\n"
    "左手捩\t左手扭\n"
    "右手捩2\t右手扭2\n"
    "左手捩2\t左手扭2\n"
    "右親指0\t右拇指0\n"
    "右親指1\t右拇指1\n"
    "右親指2\t右拇指2\n"
    "右人指1\t右食指1\n"
    "右人指2\t右食指2\n"
    "右人指3\t右食指3\n"
    "右中指1\t右中指1\n"
    "右中指2\t右中指2\n"
    "右中指3\t右中指3\n"
    "右薬指1\t右无名指1\n"
    "右薬指2\t右无名指2\n"
    "右薬指3\t右无名指3\n"
    "右小指1\t右小指1\n"
    "右小指2\t右小指2\n"
    "右小指3\t右小指3\n"
    "左親指0\t左拇指0\n"
    "左親指1\t左拇指1\n"
    "左親指2\t左拇指2\n"
    "左人指1\t左食指1\n"
    "左人指2\t左食指2\n"
    "左人指3\t左食指3\n"
    "左中指1\t左中指1\n"
    "左中指2\t左中指2\n"
    "左中指3\t左中指3\n"
    "左薬指1\t左无名指1\n"
    "左薬指2\t左无名指2\n"
    "左薬指3\t左无名指3\n"
    "左小指1\t左小指1\n"
    "左小指2\t左小指2\n"
    "左小指3\t左小指3\n"
    "右足\t右腿\n"
    "左足\t左腿\n"
    "右ひざ\t右膝\n"
    "左ひざ\t左膝\n"
    "右足首\t右脚踝\n"
    "左足首\t左脚踝\n"
    "右つま先\t右脚尖\n"
    "左つま先\t左脚尖\n"
    "右かかと\t右脚跟\n"
    "左かかと\t左脚跟\n"
    "右足D\t右腿D\n"
    "左足D\t左腿D\n"
    "右ひざD\t右膝D\n"
    "左ひざD\t左膝D\n"
    "右足首D\t右脚踝D\n"
    "左足首D\t左脚踝D\n"
    "右つま足D\t右脚尖D\n"
    "左つま足D\t左脚尖D\n"
    "右足IK\t右腿IK\n"
    "左足IK\t左腿IK\n"
    "右つま足IK\t右脚尖IK\n"
    "左つま足IK\t左脚尖IK\n"
    "足IK親\t腿IK父\n"
    "右足IK親\t右腿IK父\n"
    "左足IK親\t左腿IK父\n"
    "つま先IK\t脚尖IK\n"
    "踵IK\t脚跟IK\n"
    "ダミー\t虚拟骨\n"
    "右ダミー\t右虚拟骨\n"
    "左ダミー\t左虚拟骨\n"
    "右裾\t右裙摆\n"
    "左裾\t左裙摆\n"
    "裾\t裙摆\n"
    "# morphs\n"
    "まばたき\t眨眼\n"
    "ウィンク\t单眼眨\n"
    "ウインク\t单眼眨\n"
    "ウィンク右\t右眨眼\n"
    "ウィンク左\t左眨眼\n"
    "ウインク右\t右眨眼\n"
    "ウインク左\t左眨眼\n"
    "なごみ\t微笑\n"
    "にこり\t欢笑\n"
    "にやり\t坏笑\n"
    "笑い顔\t笑脸\n"
    "困る\t为难\n"
    "じと目\t无奈眼\n"
    "ｷﾘｯ\t锐利眼\n"
    "キリッ\t锐利眼\n"
    "びっくり\t惊讶\n"
    "真面目\t认真\n"
    "照れ\t害羞\n"
    "青ざめ\t脸色苍白\n"
    "汗\t流汗\n"
    "なみだ目\t含泪眼\n"
    "はちゅ目\t凸眼\n"
    "瞳小\t瞳孔缩小\n"
    "瞳大\t瞳孔放大\n"
    "眉上\t眉上移\n"
    "眉下\t眉下移\n"
    "あ\t啊\n"
    "い\t衣\n"
    "う\t呜\n"
    "え\t诶\n"
    "お\t哦\n"
    "ん\t嗯\n"
    "あ2\t啊2\n"
    "あ3\t啊3\n"
    "# materials\n"
    "肌\t皮肤\n"
    "顔\t脸\n"
    "お顔\t脸\n"
    "体\t身体\n"
    "目\t眼睛\n"
    "白目\t眼白\n"
    "まつげ\t睫毛\n"
    "眉\t眉毛\n"
    "髪\t头发\n"
    "前髪\t刘海\n"
    "歯\t牙齿\n"
    "舌\t舌头\n"
    "口内\t口腔\n"
    "服\t衣服\n"
    "スカート\t裙子\n"
    "袖\t袖子\n"
    "靴\t鞋子\n"
    "靴下\t袜子\n"
    "ネクタイ\t领带\n"
    "リボン\t缎带\n"
    "輪郭\t轮廓\n";

typedef tinystl::unordered_map<String, String, TinySTLAllocator> Dictionary;

Dictionary &
dictionary()
{
    static Dictionary dict;
    return dict;
}

bool
addEntry(const char *begin, const char *end, Dictionary &dict)
{
    const char *tab = nullptr;
    for (const char *ptr = begin; ptr < end; ptr++) {
        if (*ptr == '\t') {
            tab = ptr;
            break;
        }
    }
    if (tab == nullptr || tab == begin || tab + 1 == end) {
        return false;
    }
    const String key(begin, static_cast<nanoem_rsize_t>(tab - begin));
    const String value(tab + 1, static_cast<nanoem_rsize_t>(end - tab - 1));
    tinystl::pair<Dictionary::iterator, bool> result = dict.insert(tinystl::make_pair(key, value));
    if (!result.second) {
        result.first->second = value;
    }
    return true;
}

nanoem_rsize_t
parseTSV(const char *data, nanoem_rsize_t length, Dictionary &dict)
{
    nanoem_rsize_t numEntries = 0;
    const char *begin = data;
    for (nanoem_rsize_t i = 0; i <= length; i++) {
        const char c = i < length ? data[i] : '\n';
        if (c == '\n' || c == '\r') {
            const char *end = data + i;
            if (begin < end && *begin != '#') {
                numEntries += addEntry(begin, end, dict) ? 1 : 0;
            }
            begin = end + 1;
        }
    }
    return numEntries;
}

bool g_active = false;
bool g_loaded = false;

} /* namespace anonymous */

void
ModelNameDictionary::load(const char *userDictionaryFilePath, const ITranslator *translator)
{
    if (g_loaded) {
        return;
    }
    g_loaded = true;
    parseTSV(kBuiltInDictionary, sizeof(kBuiltInDictionary) - 1, dictionary());
    if (userDictionaryFilePath != nullptr && userDictionaryFilePath[0] != '\0') {
        Error error;
        FileReaderScope scope(translator);
        ByteArray bytes;
        if (scope.open(URI::createFromFilePath(userDictionaryFilePath), error)) {
            FileUtils::read(scope, bytes, error);
            if (!error.hasReason() && !bytes.empty()) {
                bytes.push_back(0);
                const nanoem_rsize_t numEntries =
                    parseTSV(reinterpret_cast<const char *>(bytes.data()), bytes.size() - 1, dictionary());
                (void) numEntries;
            }
        }
    }
}

void
ModelNameDictionary::setActive(bool value) NANOEM_DECL_NOEXCEPT
{
    g_active = value;
}

bool
ModelNameDictionary::isActive() NANOEM_DECL_NOEXCEPT
{
    return g_active;
}

void
ModelNameDictionary::translate(String &name)
{
    if (g_active && !name.empty()) {
        Dictionary::const_iterator it = dictionary().find(name);
        if (it != dictionary().end()) {
            name = it->second;
        }
    }
}

} /* namespace nanoem */
