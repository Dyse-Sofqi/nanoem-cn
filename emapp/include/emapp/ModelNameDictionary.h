/*
   Copyright (c) 2015-2023 hkrn All rights reserved

   This file is part of emapp component and it's licensed under Mozilla Public License. see LICENSE.md for more details.
 */

#pragma once
#ifndef NANOEM_EMAPP_MODELNAMEDICTIONARY_H_
#define NANOEM_EMAPP_MODELNAMEDICTIONARY_H_

#include "emapp/Forward.h"

namespace nanoem {

class ITranslator;

/*! @brief 显示用模型名翻译词典。

    仅在「模型名显示语言」设为中文（词典）时激活，把界面显示缓存里的日文模型对象名
    （骨骼、变形、材质等）替换为词典中的中文译名，未命中的条目保持原名。
    词典只作用于显示层缓存，模型数据、动作绑定与保存流程仍使用原始名字。

    词典来源按优先级叠加：内置标准词典（编译进二进制），随后加载用户词典文件
    （可执行文件同目录的 model_names_user.tsv，TSV 格式：日文名\t中文名，# 开头为注释），
    用户条目可覆盖内置条目。 */
class ModelNameDictionary NANOEM_DECL_SEALED : private NonCopyable {
public:
    static void load(const char *userDictionaryFilePath, const ITranslator *translator);
    static void setActive(bool value) NANOEM_DECL_NOEXCEPT;
    static bool isActive() NANOEM_DECL_NOEXCEPT;
    static void translate(String &name);

private:
    ModelNameDictionary() = delete;
};

} /* namespace nanoem */

#endif /* NANOEM_EMAPP_MODELNAMEDICTIONARY_H_ */
