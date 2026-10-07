# 第4步：Gold标注与状态转换

冻结评估集 baking-v1.0｜制作日期 2026-10-06｜200条合成样本

以下为所有样本的Gold及确定性合并结果。Gold只提取明示意图：不由用途猜形态/质构；不展开层级；不猜相对数值；不推断币种；保留kg/oz原单位。
未修改字段只保留在合并状态中，reset丢弃旧状态。unmapped_terms为原话的连续片段。

## eval-000001

原话：只找涂抹酱这一种产品形态。

依据：产品形态明确；不推断用途。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "product_type",
      "op": "in",
      "value": null,
      "values": [
        "cream_spread"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "product_type",
      "op": "in",
      "value": null,
      "values": [
        "cream_spread"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000002

原话：我要水果风味这一大类，具体水果不限。

依据：只给大类，不猜具体风味。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "flavor_family",
      "op": "in",
      "value": null,
      "values": [
        "fruit"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "flavor_family",
      "op": "in",
      "value": null,
      "values": [
        "fruit"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000003

原话：这次只选开心果味。

依据：具体风味不重复输出父级。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "in",
      "value": null,
      "values": [
        "pistachio"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "in",
      "value": null,
      "values": [
        "pistachio"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000004

原话：要用在泡芙上，其他条件没要求。

依据：制作对象不推断夹馅或质构。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "application",
      "op": "in",
      "value": null,
      "values": [
        "choux_puff"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "application",
      "op": "in",
      "value": null,
      "values": [
        "choux_puff"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000005

原话：使用方式必须是淋面。

依据：使用方式与产品形态独立。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "use_mode",
      "op": "in",
      "value": null,
      "values": [
        "drizzle"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "use_mode",
      "op": "in",
      "value": null,
      "values": [
        "drizzle"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000006

原话：我需要有颗粒感的质构。

依据：物理质构明示。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "texture",
      "op": "in",
      "value": null,
      "values": [
        "chunky"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "texture",
      "op": "in",
      "value": null,
      "values": [
        "chunky"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000007

原话：只看标注纯素的商品。

依据：饮食声明不扩展过敏原排除。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "dietary_claim",
      "op": "in",
      "value": null,
      "values": [
        "vegan"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "dietary_claim",
      "op": "in",
      "value": null,
      "values": [
        "vegan"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000008

原话：必须排除含芝麻过敏原的商品。

依据：安全排除为硬条件。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "allergen",
      "op": "not_in",
      "value": null,
      "values": [
        "sesame"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "allergen",
      "op": "not_in",
      "value": null,
      "values": [
        "sesame"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000009

原话：未开封必须可以常温保存。

依据：未开封储存要求。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "storage",
      "op": "in",
      "value": null,
      "values": [
        "shelf_stable"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "storage",
      "op": "in",
      "value": null,
      "values": [
        "shelf_stable"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000010

原话：必须经过验证能耐烤。

依据：耐烤明确为布尔真。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "bake_stable",
      "op": "eq",
      "value": true,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "bake_stable",
      "op": "eq",
      "value": true,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000011

原话：甜度等级就选3级。

依据：明确等级，不是相对偏好。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "sweetness_level",
      "op": "eq",
      "value": 3,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "sweetness_level",
      "op": "eq",
      "value": 3,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000012

原话：风味强度至少4级。

依据：明确数值下界。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "flavor_intensity",
      "op": "gte",
      "value": 4,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "flavor_intensity",
      "op": "gte",
      "value": 4,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000013

原话：每件标价必须是18美元。

依据：精确价格及显式币种。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "price",
      "op": "eq",
      "value": 18,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "USD"
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "price",
      "op": "eq",
      "value": 18,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "USD"
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000014

原话：净含量恰好250克装。

依据：规格精确值。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "size",
      "op": "eq",
      "value": 250,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "g"
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "size",
      "op": "eq",
      "value": 250,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "g"
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000015

原话：产品形态只接受水果制品或果酱。

依据：产品形态不猜水果口味。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "product_type",
      "op": "in",
      "value": null,
      "values": [
        "fruit_preparation"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "product_type",
      "op": "in",
      "value": null,
      "values": [
        "fruit_preparation"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000016

原话：风味指定为black sesame。

依据：英文别名映射，不输出未知值。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "in",
      "value": null,
      "values": [
        "black_sesame"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "in",
      "value": null,
      "values": [
        "black_sesame"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000017

原话：拿来做macaron，其他随意。

依据：英文制作对象。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "application",
      "op": "in",
      "value": null,
      "values": [
        "macaron"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "application",
      "op": "in",
      "value": null,
      "values": [
        "macaron"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000018

原话：需要标明无麸质的。

依据：声明不自行增加wheat排除。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "dietary_claim",
      "op": "in",
      "value": null,
      "values": [
        "gluten_free"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "dietary_claim",
      "op": "in",
      "value": null,
      "values": [
        "gluten_free"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000019

原话：只接受未开封冷冻储存的。

依据：储存枚举映射。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "storage",
      "op": "in",
      "value": null,
      "values": [
        "frozen"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "storage",
      "op": "in",
      "value": null,
      "values": [
        "frozen"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000020

原话：商品必须明确标注不耐烤。

依据：明确假值；未知属性不等于假。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "bake_stable",
      "op": "eq",
      "value": false,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "bake_stable",
      "op": "eq",
      "value": false,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000021

原话：做可颂夹馅用，两个条件都必须满足。

依据：只提取明示的多个硬条件；并列用途不推导额外属性。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "application",
      "op": "in",
      "value": null,
      "values": [
        "croissant_pastry"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "use_mode",
      "op": "in",
      "value": null,
      "values": [
        "fill"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "application",
      "op": "in",
      "value": null,
      "values": [
        "croissant_pastry"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "use_mode",
      "op": "in",
      "value": null,
      "values": [
        "fill"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000022

原话：要抹茶味，并且未开封常温保存。

依据：只提取明示的多个硬条件；并列用途不推导额外属性。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "in",
      "value": null,
      "values": [
        "matcha"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "storage",
      "op": "in",
      "value": null,
      "values": [
        "shelf_stable"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "in",
      "value": null,
      "values": [
        "matcha"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "storage",
      "op": "in",
      "value": null,
      "values": [
        "shelf_stable"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000023

原话：选淋酱这种形态，质构必须流动型。

依据：只提取明示的多个硬条件；并列用途不推导额外属性。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "product_type",
      "op": "in",
      "value": null,
      "values": [
        "sauce_topping"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "texture",
      "op": "in",
      "value": null,
      "values": [
        "pourable"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "product_type",
      "op": "in",
      "value": null,
      "values": [
        "sauce_topping"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "texture",
      "op": "in",
      "value": null,
      "values": [
        "pourable"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000024

原话：必须是纯素商品，而且排除含花生过敏原的。

依据：只提取明示的多个硬条件；并列用途不推导额外属性。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "dietary_claim",
      "op": "in",
      "value": null,
      "values": [
        "vegan"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "allergen",
      "op": "not_in",
      "value": null,
      "values": [
        "peanut"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "dietary_claim",
      "op": "in",
      "value": null,
      "values": [
        "vegan"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "allergen",
      "op": "not_in",
      "value": null,
      "values": [
        "peanut"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000025

原话：只要黑巧克力味，甜度最多2级。

依据：只提取明示的多个硬条件；并列用途不推导额外属性。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "in",
      "value": null,
      "values": [
        "dark_chocolate"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "sweetness_level",
      "op": "lte",
      "value": 2,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "in",
      "value": null,
      "values": [
        "dark_chocolate"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "sweetness_level",
      "op": "lte",
      "value": 2,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000026

原话：必须用于蛋糕，且要可裱挤的质构。

依据：只提取明示的多个硬条件；并列用途不推导额外属性。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "application",
      "op": "in",
      "value": null,
      "values": [
        "cake_cupcake"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "texture",
      "op": "in",
      "value": null,
      "values": [
        "pipeable"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "application",
      "op": "in",
      "value": null,
      "values": [
        "cake_cupcake"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "texture",
      "op": "in",
      "value": null,
      "values": [
        "pipeable"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000027

原话：单件不超过22美元，至少500克装。

依据：只提取明示的多个硬条件；并列用途不推导额外属性。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "price",
      "op": "lte",
      "value": 22,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "USD"
    },
    {
      "field": "size",
      "op": "gte",
      "value": 500,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "g"
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "price",
      "op": "lte",
      "value": 22,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "USD"
    },
    {
      "field": "size",
      "op": "gte",
      "value": 500,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "g"
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000028

原话：只能选水果大类，而且要无乳制品声明。

依据：只提取明示的多个硬条件；并列用途不推导额外属性。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "flavor_family",
      "op": "in",
      "value": null,
      "values": [
        "fruit"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "dietary_claim",
      "op": "in",
      "value": null,
      "values": [
        "dairy_free"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "flavor_family",
      "op": "in",
      "value": null,
      "values": [
        "fruit"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "dietary_claim",
      "op": "in",
      "value": null,
      "values": [
        "dairy_free"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000029

原话：草莓或蓝莓都行，但必须是果酱形态。

依据：只提取明示的多个硬条件；并列用途不推导额外属性。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "in",
      "value": null,
      "values": [
        "strawberry",
        "blueberry"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "product_type",
      "op": "in",
      "value": null,
      "values": [
        "fruit_preparation"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "in",
      "value": null,
      "values": [
        "strawberry",
        "blueberry"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "product_type",
      "op": "in",
      "value": null,
      "values": [
        "fruit_preparation"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000030

原话：用于曲奇一起烘烤，商品必须验证耐烤。

依据：只提取明示的多个硬条件；并列用途不推导额外属性。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "application",
      "op": "in",
      "value": null,
      "values": [
        "cookie_biscuit"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "use_mode",
      "op": "in",
      "value": null,
      "values": [
        "bake_in"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "bake_stable",
      "op": "eq",
      "value": true,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "application",
      "op": "in",
      "value": null,
      "values": [
        "cookie_biscuit"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "use_mode",
      "op": "in",
      "value": null,
      "values": [
        "bake_in"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "bake_stable",
      "op": "eq",
      "value": true,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000031

原话：要可挤压质构，并且未开封冷藏。

依据：只提取明示的多个硬条件；并列用途不推导额外属性。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "texture",
      "op": "in",
      "value": null,
      "values": [
        "squeezable"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "storage",
      "op": "in",
      "value": null,
      "values": [
        "refrigerated"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "texture",
      "op": "in",
      "value": null,
      "values": [
        "squeezable"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "storage",
      "op": "in",
      "value": null,
      "values": [
        "refrigerated"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000032

原话：找咖啡味的，使用方式必须是拌入。

依据：只提取明示的多个硬条件；并列用途不推导额外属性。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "in",
      "value": null,
      "values": [
        "coffee"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "use_mode",
      "op": "in",
      "value": null,
      "values": [
        "swirl"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "in",
      "value": null,
      "values": [
        "coffee"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "use_mode",
      "op": "in",
      "value": null,
      "values": [
        "swirl"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000033

原话：需要无蛋声明，风味强度限定2到4级。

依据：只提取明示的多个硬条件；并列用途不推导额外属性。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "dietary_claim",
      "op": "in",
      "value": null,
      "values": [
        "egg_free"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "flavor_intensity",
      "op": "between",
      "value": null,
      "values": [],
      "min_value": 2,
      "max_value": 4,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "dietary_claim",
      "op": "in",
      "value": null,
      "values": [
        "egg_free"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "flavor_intensity",
      "op": "between",
      "value": null,
      "values": [],
      "min_value": 2,
      "max_value": 4,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000034

原话：用于面包涂抹，不接受有颗粒的质构。

依据：只提取明示的多个硬条件；并列用途不推导额外属性。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "application",
      "op": "in",
      "value": null,
      "values": [
        "bread_toast"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "use_mode",
      "op": "in",
      "value": null,
      "values": [
        "spread"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "texture",
      "op": "not_in",
      "value": null,
      "values": [
        "chunky"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "application",
      "op": "in",
      "value": null,
      "values": [
        "bread_toast"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "use_mode",
      "op": "in",
      "value": null,
      "values": [
        "spread"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "texture",
      "op": "not_in",
      "value": null,
      "values": [
        "chunky"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000035

原话：选夹馅酱形态、香草味和1公斤装，都是硬要求。

依据：只提取明示的多个硬条件；并列用途不推导额外属性。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "product_type",
      "op": "in",
      "value": null,
      "values": [
        "filling_paste"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "flavor",
      "op": "in",
      "value": null,
      "values": [
        "vanilla"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "size",
      "op": "eq",
      "value": 1,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "kg"
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "product_type",
      "op": "in",
      "value": null,
      "values": [
        "filling_paste"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "flavor",
      "op": "in",
      "value": null,
      "values": [
        "vanilla"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "size",
      "op": "eq",
      "value": 1,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "kg"
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000036

原话：必须用于可颂夹心，口味最好是开心果。

依据：必须/只能作为硬条件，最好/优先/尽量作为软偏好；不猜数值。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "application",
      "op": "in",
      "value": null,
      "values": [
        "croissant_pastry"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "use_mode",
      "op": "in",
      "value": null,
      "values": [
        "fill"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [
    {
      "field": "flavor",
      "preference": "prefer",
      "value": null,
      "values": [
        "pistachio"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "application",
      "op": "in",
      "value": null,
      "values": [
        "croissant_pastry"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "use_mode",
      "op": "in",
      "value": null,
      "values": [
        "fill"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [
    {
      "field": "flavor",
      "preference": "prefer",
      "value": null,
      "values": [
        "pistachio"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "sort": null
}
```

## eval-000037

原话：预算上限20美元，甜度希望低一点。

依据：必须/只能作为硬条件，最好/优先/尽量作为软偏好；不猜数值。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "price",
      "op": "lte",
      "value": 20,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "USD"
    }
  ],
  "soft_preferences": [
    {
      "field": "sweetness_level",
      "preference": "lower",
      "value": null,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "price",
      "op": "lte",
      "value": 20,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "USD"
    }
  ],
  "soft_preferences": [
    {
      "field": "sweetness_level",
      "preference": "lower",
      "value": null,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "sort": null
}
```

## eval-000038

原话：必须是淋酱，最好是流动型质构。

依据：必须/只能作为硬条件，最好/优先/尽量作为软偏好；不猜数值。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "product_type",
      "op": "in",
      "value": null,
      "values": [
        "sauce_topping"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [
    {
      "field": "texture",
      "preference": "prefer",
      "value": null,
      "values": [
        "pourable"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "product_type",
      "op": "in",
      "value": null,
      "values": [
        "sauce_topping"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [
    {
      "field": "texture",
      "preference": "prefer",
      "value": null,
      "values": [
        "pourable"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "sort": null
}
```

## eval-000039

原话：标明纯素是必须的，风味优先抹茶。

依据：必须/只能作为硬条件，最好/优先/尽量作为软偏好；不猜数值。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "dietary_claim",
      "op": "in",
      "value": null,
      "values": [
        "vegan"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [
    {
      "field": "flavor",
      "preference": "prefer",
      "value": null,
      "values": [
        "matcha"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "dietary_claim",
      "op": "in",
      "value": null,
      "values": [
        "vegan"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [
    {
      "field": "flavor",
      "preference": "prefer",
      "value": null,
      "values": [
        "matcha"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "sort": null
}
```

## eval-000040

原话：必须排除牛奶过敏原，最好常温保存。

依据：必须/只能作为硬条件，最好/优先/尽量作为软偏好；不猜数值。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "allergen",
      "op": "not_in",
      "value": null,
      "values": [
        "milk"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [
    {
      "field": "storage",
      "preference": "prefer",
      "value": null,
      "values": [
        "shelf_stable"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "allergen",
      "op": "not_in",
      "value": null,
      "values": [
        "milk"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [
    {
      "field": "storage",
      "preference": "prefer",
      "value": null,
      "values": [
        "shelf_stable"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "sort": null
}
```

## eval-000041

原话：规格至少500克，价格希望低一些。

依据：必须/只能作为硬条件，最好/优先/尽量作为软偏好；不猜数值。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "size",
      "op": "gte",
      "value": 500,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "g"
    }
  ],
  "soft_preferences": [
    {
      "field": "price",
      "preference": "lower",
      "value": null,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "size",
      "op": "gte",
      "value": 500,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "g"
    }
  ],
  "soft_preferences": [
    {
      "field": "price",
      "preference": "lower",
      "value": null,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "sort": null
}
```

## eval-000042

原话：商品必须耐烤，风味强度希望高一点。

依据：必须/只能作为硬条件，最好/优先/尽量作为软偏好；不猜数值。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "bake_stable",
      "op": "eq",
      "value": true,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [
    {
      "field": "flavor_intensity",
      "preference": "higher",
      "value": null,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "bake_stable",
      "op": "eq",
      "value": true,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [
    {
      "field": "flavor_intensity",
      "preference": "higher",
      "value": null,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "sort": null
}
```

## eval-000043

原话：必须用于蛋糕，尽量避开咖啡味。

依据：必须/只能作为硬条件，最好/优先/尽量作为软偏好；不猜数值。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "application",
      "op": "in",
      "value": null,
      "values": [
        "cake_cupcake"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [
    {
      "field": "flavor",
      "preference": "avoid",
      "value": null,
      "values": [
        "coffee"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "application",
      "op": "in",
      "value": null,
      "values": [
        "cake_cupcake"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [
    {
      "field": "flavor",
      "preference": "avoid",
      "value": null,
      "values": [
        "coffee"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "sort": null
}
```

## eval-000044

原话：甜度必须1到3级，最好带水果风味。

依据：必须/只能作为硬条件，最好/优先/尽量作为软偏好；不猜数值。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "sweetness_level",
      "op": "between",
      "value": null,
      "values": [],
      "min_value": 1,
      "max_value": 3,
      "unit": null
    }
  ],
  "soft_preferences": [
    {
      "field": "flavor_family",
      "preference": "prefer",
      "value": null,
      "values": [
        "fruit"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "sweetness_level",
      "op": "between",
      "value": null,
      "values": [],
      "min_value": 1,
      "max_value": 3,
      "unit": null
    }
  ],
  "soft_preferences": [
    {
      "field": "flavor_family",
      "preference": "prefer",
      "value": null,
      "values": [
        "fruit"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "sort": null
}
```

## eval-000045

原话：必须有无麸质声明，使用方式最好是涂抹。

依据：必须/只能作为硬条件，最好/优先/尽量作为软偏好；不猜数值。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "dietary_claim",
      "op": "in",
      "value": null,
      "values": [
        "gluten_free"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [
    {
      "field": "use_mode",
      "preference": "prefer",
      "value": null,
      "values": [
        "spread"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "dietary_claim",
      "op": "in",
      "value": null,
      "values": [
        "gluten_free"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [
    {
      "field": "use_mode",
      "preference": "prefer",
      "value": null,
      "values": [
        "spread"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "sort": null
}
```

## eval-000046

原话：选草莓味是硬要求，净含量最好约8盎司。

依据：必须/只能作为硬条件，最好/优先/尽量作为软偏好；不猜数值。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "in",
      "value": null,
      "values": [
        "strawberry"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [
    {
      "field": "size",
      "preference": "around",
      "value": 8,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "oz"
    }
  ],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "in",
      "value": null,
      "values": [
        "strawberry"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [
    {
      "field": "size",
      "preference": "around",
      "value": 8,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "oz"
    }
  ],
  "sort": null
}
```

## eval-000047

原话：只能选未开封冷藏的，产品形态最好是涂抹酱。

依据：必须/只能作为硬条件，最好/优先/尽量作为软偏好；不猜数值。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "storage",
      "op": "in",
      "value": null,
      "values": [
        "refrigerated"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [
    {
      "field": "product_type",
      "preference": "prefer",
      "value": null,
      "values": [
        "cream_spread"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "storage",
      "op": "in",
      "value": null,
      "values": [
        "refrigerated"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [
    {
      "field": "product_type",
      "preference": "prefer",
      "value": null,
      "values": [
        "cream_spread"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "sort": null
}
```

## eval-000048

原话：必须用于泡芙，最好有无蛋声明。

依据：必须/只能作为硬条件，最好/优先/尽量作为软偏好；不猜数值。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "application",
      "op": "in",
      "value": null,
      "values": [
        "choux_puff"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [
    {
      "field": "dietary_claim",
      "preference": "prefer",
      "value": null,
      "values": [
        "egg_free"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "application",
      "op": "in",
      "value": null,
      "values": [
        "choux_puff"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [
    {
      "field": "dietary_claim",
      "preference": "prefer",
      "value": null,
      "values": [
        "egg_free"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "sort": null
}
```

## eval-000049

原话：必须有颗粒，价格最好在12到18美元之间。

依据：必须/只能作为硬条件，最好/优先/尽量作为软偏好；不猜数值。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "texture",
      "op": "in",
      "value": null,
      "values": [
        "chunky"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [
    {
      "field": "price",
      "preference": "between",
      "value": null,
      "values": [],
      "min_value": 12,
      "max_value": 18,
      "unit": "USD"
    }
  ],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "texture",
      "op": "in",
      "value": null,
      "values": [
        "chunky"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [
    {
      "field": "price",
      "preference": "between",
      "value": null,
      "values": [],
      "min_value": 12,
      "max_value": 18,
      "unit": "USD"
    }
  ],
  "sort": null
}
```

## eval-000050

原话：风味必须是焙茶，甜度最好在2到3级之间。

依据：必须/只能作为硬条件，最好/优先/尽量作为软偏好；不猜数值。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "in",
      "value": null,
      "values": [
        "hojicha"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [
    {
      "field": "sweetness_level",
      "preference": "between",
      "value": null,
      "values": [],
      "min_value": 2,
      "max_value": 3,
      "unit": null
    }
  ],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "in",
      "value": null,
      "values": [
        "hojicha"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [
    {
      "field": "sweetness_level",
      "preference": "between",
      "value": null,
      "values": [],
      "min_value": 2,
      "max_value": 3,
      "unit": null
    }
  ],
  "sort": null
}
```

## eval-000051

原话：必须是500克装，最好不要冷冻储存。

依据：必须/只能作为硬条件，最好/优先/尽量作为软偏好；不猜数值。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "size",
      "op": "eq",
      "value": 500,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "g"
    }
  ],
  "soft_preferences": [
    {
      "field": "storage",
      "preference": "avoid",
      "value": null,
      "values": [
        "frozen"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "size",
      "op": "eq",
      "value": 500,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "g"
    }
  ],
  "soft_preferences": [
    {
      "field": "storage",
      "preference": "avoid",
      "value": null,
      "values": [
        "frozen"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "sort": null
}
```

## eval-000052

原话：必须用于冰淇淋，风味强度最好约3级。

依据：必须/只能作为硬条件，最好/优先/尽量作为软偏好；不猜数值。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "application",
      "op": "in",
      "value": null,
      "values": [
        "ice_cream_frozen"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [
    {
      "field": "flavor_intensity",
      "preference": "around",
      "value": 3,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "application",
      "op": "in",
      "value": null,
      "values": [
        "ice_cream_frozen"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [
    {
      "field": "flavor_intensity",
      "preference": "around",
      "value": 3,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "sort": null
}
```

## eval-000053

原话：必须是奶油酱形态，尽量不选勺取型质构。

依据：必须/只能作为硬条件，最好/优先/尽量作为软偏好；不猜数值。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "product_type",
      "op": "in",
      "value": null,
      "values": [
        "cream_spread"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [
    {
      "field": "texture",
      "preference": "avoid",
      "value": null,
      "values": [
        "spoonable"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "product_type",
      "op": "in",
      "value": null,
      "values": [
        "cream_spread"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [
    {
      "field": "texture",
      "preference": "avoid",
      "value": null,
      "values": [
        "spoonable"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "sort": null
}
```

## eval-000054

原话：预算不得超过16美元，最好用于塔派。

依据：必须/只能作为硬条件，最好/优先/尽量作为软偏好；不猜数值。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "price",
      "op": "lte",
      "value": 16,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "USD"
    }
  ],
  "soft_preferences": [
    {
      "field": "application",
      "preference": "prefer",
      "value": null,
      "values": [
        "tart_pie"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "price",
      "op": "lte",
      "value": 16,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "USD"
    }
  ],
  "soft_preferences": [
    {
      "field": "application",
      "preference": "prefer",
      "value": null,
      "values": [
        "tart_pie"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "sort": null
}
```

## eval-000055

原话：必须排除鸡蛋过敏原，风味优先香草或卡仕达。

依据：必须/只能作为硬条件，最好/优先/尽量作为软偏好；不猜数值。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "allergen",
      "op": "not_in",
      "value": null,
      "values": [
        "egg"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [
    {
      "field": "flavor",
      "preference": "prefer",
      "value": null,
      "values": [
        "vanilla",
        "custard"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "allergen",
      "op": "not_in",
      "value": null,
      "values": [
        "egg"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [
    {
      "field": "flavor",
      "preference": "prefer",
      "value": null,
      "values": [
        "vanilla",
        "custard"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "sort": null
}
```

## eval-000056

原话：不要焦糖味，其他风味没限制。

依据：否定只作用于明示字段；尽量回避为avoid，硬排除为not_in。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "not_in",
      "value": null,
      "values": [
        "caramel"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "not_in",
      "value": null,
      "values": [
        "caramel"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000057

原话：尽量避开榛子味，但不是硬性要求。

依据：否定只作用于明示字段；尽量回避为avoid，硬排除为not_in。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [],
  "soft_preferences": [
    {
      "field": "flavor",
      "preference": "avoid",
      "value": null,
      "values": [
        "hazelnut"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [],
  "soft_preferences": [
    {
      "field": "flavor",
      "preference": "avoid",
      "value": null,
      "values": [
        "hazelnut"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "sort": null
}
```

## eval-000058

原话：排除冷冻储存的商品。

依据：否定只作用于明示字段；尽量回避为avoid，硬排除为not_in。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "storage",
      "op": "not_in",
      "value": null,
      "values": [
        "frozen"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "storage",
      "op": "not_in",
      "value": null,
      "values": [
        "frozen"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000059

原话：最好别选淋酱这种形态。

依据：否定只作用于明示字段；尽量回避为avoid，硬排除为not_in。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [],
  "soft_preferences": [
    {
      "field": "product_type",
      "preference": "avoid",
      "value": null,
      "values": [
        "sauce_topping"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [],
  "soft_preferences": [
    {
      "field": "product_type",
      "preference": "avoid",
      "value": null,
      "values": [
        "sauce_topping"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "sort": null
}
```

## eval-000060

原话：不要颗粒质构。

依据：否定只作用于明示字段；尽量回避为avoid，硬排除为not_in。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "texture",
      "op": "not_in",
      "value": null,
      "values": [
        "chunky"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "texture",
      "op": "not_in",
      "value": null,
      "values": [
        "chunky"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000061

原话：尽量不用涂抹这种使用方式。

依据：否定只作用于明示字段；尽量回避为avoid，硬排除为not_in。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [],
  "soft_preferences": [
    {
      "field": "use_mode",
      "preference": "avoid",
      "value": null,
      "values": [
        "spread"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [],
  "soft_preferences": [
    {
      "field": "use_mode",
      "preference": "avoid",
      "value": null,
      "values": [
        "spread"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "sort": null
}
```

## eval-000062

原话：不要茶与咖啡这一整个风味大类。

依据：否定只作用于明示字段；尽量回避为avoid，硬排除为not_in。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "flavor_family",
      "op": "not_in",
      "value": null,
      "values": [
        "tea_coffee"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "flavor_family",
      "op": "not_in",
      "value": null,
      "values": [
        "tea_coffee"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000063

原话：最好不要用于咖啡饮品。

依据：否定只作用于明示字段；尽量回避为avoid，硬排除为not_in。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [],
  "soft_preferences": [
    {
      "field": "application",
      "preference": "avoid",
      "value": null,
      "values": [
        "coffee_drink"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [],
  "soft_preferences": [
    {
      "field": "application",
      "preference": "avoid",
      "value": null,
      "values": [
        "coffee_drink"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "sort": null
}
```

## eval-000064

原话：不看带纯素声明的商品。

依据：否定只作用于明示字段；尽量回避为avoid，硬排除为not_in。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "dietary_claim",
      "op": "not_in",
      "value": null,
      "values": [
        "vegan"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "dietary_claim",
      "op": "not_in",
      "value": null,
      "values": [
        "vegan"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000065

原话：不要红豆味，也不要紫薯味。

依据：否定只作用于明示字段；尽量回避为avoid，硬排除为not_in。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "not_in",
      "value": null,
      "values": [
        "red_bean",
        "purple_sweet_potato"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "not_in",
      "value": null,
      "values": [
        "red_bean",
        "purple_sweet_potato"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000066

原话：我对花生过敏，必须排除含花生过敏原的产品。

依据：过敏原排除与风味排除独立；不扩展父子枚举，展开由运行时处理。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "allergen",
      "op": "not_in",
      "value": null,
      "values": [
        "peanut"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "allergen",
      "op": "not_in",
      "value": null,
      "values": [
        "peanut"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000067

原话：只是不要花生味，没有提出过敏要求。

依据：过敏原排除与风味排除独立；不扩展父子枚举，展开由运行时处理。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "not_in",
      "value": null,
      "values": [
        "peanut"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "not_in",
      "value": null,
      "values": [
        "peanut"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000068

原话：我对开心果过敏，必须排除开心果过敏原。

依据：过敏原排除与风味排除独立；不扩展父子枚举，展开由运行时处理。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "allergen",
      "op": "not_in",
      "value": null,
      "values": [
        "pistachio"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "allergen",
      "op": "not_in",
      "value": null,
      "values": [
        "pistachio"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000069

原话：开心果味不喜欢，请排除这种口味。

依据：过敏原排除与风味排除独立；不扩展父子枚举，展开由运行时处理。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "not_in",
      "value": null,
      "values": [
        "pistachio"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "not_in",
      "value": null,
      "values": [
        "pistachio"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000070

原话：榛子过敏，请过滤含榛子过敏原的。

依据：过敏原排除与风味排除独立；不扩展父子枚举，展开由运行时处理。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "allergen",
      "op": "not_in",
      "value": null,
      "values": [
        "hazelnut"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "allergen",
      "op": "not_in",
      "value": null,
      "values": [
        "hazelnut"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000071

原话：不要榛子风味，仅仅是口味选择。

依据：过敏原排除与风味排除独立；不扩展父子枚举，展开由运行时处理。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "not_in",
      "value": null,
      "values": [
        "hazelnut"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "not_in",
      "value": null,
      "values": [
        "hazelnut"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000072

原话：对杏仁过敏，含杏仁过敏原的不能要。

依据：过敏原排除与风味排除独立；不扩展父子枚举，展开由运行时处理。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "allergen",
      "op": "not_in",
      "value": null,
      "values": [
        "almond"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "allergen",
      "op": "not_in",
      "value": null,
      "values": [
        "almond"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000073

原话：杏仁味排除掉，不要追加其他限制。

依据：过敏原排除与风味排除独立；不扩展父子枚举，展开由运行时处理。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "not_in",
      "value": null,
      "values": [
        "almond"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "not_in",
      "value": null,
      "values": [
        "almond"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000074

原话：必须排除树坚果过敏原。

依据：过敏原排除与风味排除独立；不扩展父子枚举，展开由运行时处理。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "allergen",
      "op": "not_in",
      "value": null,
      "values": [
        "tree_nut"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "allergen",
      "op": "not_in",
      "value": null,
      "values": [
        "tree_nut"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000075

原话：牛奶过敏，请排除牛奶过敏原。

依据：过敏原排除与风味排除独立；不扩展父子枚举，展开由运行时处理。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "allergen",
      "op": "not_in",
      "value": null,
      "values": [
        "milk"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "allergen",
      "op": "not_in",
      "value": null,
      "values": [
        "milk"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000076

原话：对鸡蛋过敏，排除鸡蛋过敏原。

依据：过敏原排除与风味排除独立；不扩展父子枚举，展开由运行时处理。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "allergen",
      "op": "not_in",
      "value": null,
      "values": [
        "egg"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "allergen",
      "op": "not_in",
      "value": null,
      "values": [
        "egg"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000077

原话：小麦过敏，含小麦过敏原的不能买。

依据：过敏原排除与风味排除独立；不扩展父子枚举，展开由运行时处理。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "allergen",
      "op": "not_in",
      "value": null,
      "values": [
        "wheat"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "allergen",
      "op": "not_in",
      "value": null,
      "values": [
        "wheat"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000078

原话：对大豆过敏，必须排除大豆过敏原。

依据：过敏原排除与风味排除独立；不扩展父子枚举，展开由运行时处理。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "allergen",
      "op": "not_in",
      "value": null,
      "values": [
        "soy"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "allergen",
      "op": "not_in",
      "value": null,
      "values": [
        "soy"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000079

原话：芝麻过敏，筛掉含芝麻过敏原的。

依据：过敏原排除与风味排除独立；不扩展父子枚举，展开由运行时处理。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "allergen",
      "op": "not_in",
      "value": null,
      "values": [
        "sesame"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "allergen",
      "op": "not_in",
      "value": null,
      "values": [
        "sesame"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000080

原话：不要黑芝麻味的，我只是在选口味。

依据：过敏原排除与风味排除独立；不扩展父子枚举，展开由运行时处理。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "not_in",
      "value": null,
      "values": [
        "black_sesame"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "not_in",
      "value": null,
      "values": [
        "black_sesame"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000081

原话：腰果过敏，排除腰果过敏原，不扩大范围。

依据：过敏原排除与风味排除独立；不扩展父子枚举，展开由运行时处理。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "allergen",
      "op": "not_in",
      "value": null,
      "values": [
        "cashew"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "allergen",
      "op": "not_in",
      "value": null,
      "values": [
        "cashew"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000082

原话：核桃过敏，必须排除核桃过敏原。

依据：过敏原排除与风味排除独立；不扩展父子枚举，展开由运行时处理。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "allergen",
      "op": "not_in",
      "value": null,
      "values": [
        "walnut"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "allergen",
      "op": "not_in",
      "value": null,
      "values": [
        "walnut"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000083

原话：我对花生和鸡蛋过敏，二者都必须排除。

依据：过敏原排除与风味排除独立；不扩展父子枚举，展开由运行时处理。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "allergen",
      "op": "not_in",
      "value": null,
      "values": [
        "peanut",
        "egg"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "allergen",
      "op": "not_in",
      "value": null,
      "values": [
        "peanut",
        "egg"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000084

原话：牛奶及大豆过敏原都不接受。

依据：过敏原排除与风味排除独立；不扩展父子枚举，展开由运行时处理。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "allergen",
      "op": "not_in",
      "value": null,
      "values": [
        "milk",
        "soy"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "allergen",
      "op": "not_in",
      "value": null,
      "values": [
        "milk",
        "soy"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000085

原话：排除花生味和榛子味，别把口味偏好当过敏。

依据：过敏原排除与风味排除独立；不扩展父子枚举，展开由运行时处理。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "not_in",
      "value": null,
      "values": [
        "peanut",
        "hazelnut"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "not_in",
      "value": null,
      "values": [
        "peanut",
        "hazelnut"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000086

原话：花生过敏必须排除花生过敏原，同时口味必须是黑巧克力。

依据：安全条件与风味条件分别提取，不能互相替代。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "allergen",
      "op": "not_in",
      "value": null,
      "values": [
        "peanut"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "flavor",
      "op": "in",
      "value": null,
      "values": [
        "dark_chocolate"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "allergen",
      "op": "not_in",
      "value": null,
      "values": [
        "peanut"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "flavor",
      "op": "in",
      "value": null,
      "values": [
        "dark_chocolate"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000087

原话：必须排除牛奶过敏原，另外不要牛奶巧克力味。

依据：分别明示两个排除意图，两个字段都保留。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "allergen",
      "op": "not_in",
      "value": null,
      "values": [
        "milk"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "flavor",
      "op": "not_in",
      "value": null,
      "values": [
        "milk_chocolate"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "allergen",
      "op": "not_in",
      "value": null,
      "values": [
        "milk"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "flavor",
      "op": "not_in",
      "value": null,
      "values": [
        "milk_chocolate"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000088

原话：尽量避开花生味，其他没有限制。

依据：普通风味软回避，不添加allergen。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [],
  "soft_preferences": [
    {
      "field": "flavor",
      "preference": "avoid",
      "value": null,
      "values": [
        "peanut"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [],
  "soft_preferences": [
    {
      "field": "flavor",
      "preference": "avoid",
      "value": null,
      "values": [
        "peanut"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "sort": null
}
```

## eval-000089

原话：开心果味是必须的，但必须排除花生过敏原。

依据：花生安全限制不扩大为所有树坚果。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "in",
      "value": null,
      "values": [
        "pistachio"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "allergen",
      "op": "not_in",
      "value": null,
      "values": [
        "peanut"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "in",
      "value": null,
      "values": [
        "pistachio"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "allergen",
      "op": "not_in",
      "value": null,
      "values": [
        "peanut"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000090

原话：花生过敏必须排除花生过敏原，最好选草莓味。

依据：安全限制是硬条件，最好口味是软偏好。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "allergen",
      "op": "not_in",
      "value": null,
      "values": [
        "peanut"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [
    {
      "field": "flavor",
      "preference": "prefer",
      "value": null,
      "values": [
        "strawberry"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "allergen",
      "op": "not_in",
      "value": null,
      "values": [
        "peanut"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [
    {
      "field": "flavor",
      "preference": "prefer",
      "value": null,
      "values": [
        "strawberry"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "sort": null
}
```

## eval-000091

原话：口味改成必须抹茶，原来的口味条件取消。

依据：同一字段新条件整体替换旧hard/soft；不把替换表达成clear加set。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "in",
      "value": null,
      "values": [
        "matcha"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "in",
      "value": null,
      "values": [
        "matcha"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000092

原话：原来的口味硬要求改为最好草莓。

依据：同一字段新条件整体替换旧hard/soft；不把替换表达成clear加set。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [],
  "soft_preferences": [
    {
      "field": "flavor",
      "preference": "prefer",
      "value": null,
      "values": [
        "strawberry"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [],
  "soft_preferences": [
    {
      "field": "flavor",
      "preference": "prefer",
      "value": null,
      "values": [
        "strawberry"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "sort": null
}
```

## eval-000093

原话：口味现在必须是黑巧，原先软偏好不保留。

依据：同一字段新条件整体替换旧hard/soft；不把替换表达成clear加set。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "in",
      "value": null,
      "values": [
        "dark_chocolate"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "in",
      "value": null,
      "values": [
        "dark_chocolate"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000094

原话：预算上限改为30美元。

依据：同一字段新条件整体替换旧hard/soft；不把替换表达成clear加set。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "price",
      "op": "lte",
      "value": 30,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "USD"
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "price",
      "op": "lte",
      "value": 30,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "USD"
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000095

原话：包装改成恰好1公斤装。

依据：同一字段新条件整体替换旧hard/soft；不把替换表达成clear加set。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "size",
      "op": "eq",
      "value": 1,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "kg"
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "size",
      "op": "eq",
      "value": 1,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "kg"
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000096

原话：储存要求换成必须冷藏。

依据：同一字段新条件整体替换旧hard/soft；不把替换表达成clear加set。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "storage",
      "op": "in",
      "value": null,
      "values": [
        "refrigerated"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "storage",
      "op": "in",
      "value": null,
      "values": [
        "refrigerated"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000097

原话：质构改成必须有颗粒。

依据：同一字段新条件整体替换旧hard/soft；不把替换表达成clear加set。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "texture",
      "op": "in",
      "value": null,
      "values": [
        "chunky"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "texture",
      "op": "in",
      "value": null,
      "values": [
        "chunky"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000098

原话：产品形态换成淋酱，作为硬要求。

依据：同一字段新条件整体替换旧hard/soft；不把替换表达成clear加set。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "product_type",
      "op": "in",
      "value": null,
      "values": [
        "sauce_topping"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "product_type",
      "op": "in",
      "value": null,
      "values": [
        "sauce_topping"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000099

原话：用途改成必须用于马卡龙。

依据：同一字段新条件整体替换旧hard/soft；不把替换表达成clear加set。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "application",
      "op": "in",
      "value": null,
      "values": [
        "macaron"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "application",
      "op": "in",
      "value": null,
      "values": [
        "macaron"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000100

原话：使用方式换成必须淋面。

依据：同一字段新条件整体替换旧hard/soft；不把替换表达成clear加set。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "use_mode",
      "op": "in",
      "value": null,
      "values": [
        "drizzle"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "use_mode",
      "op": "in",
      "value": null,
      "values": [
        "drizzle"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000101

原话：甜度改成最多2级，不保留原来甜度条件。

依据：同一字段新条件整体替换旧hard/soft；不把替换表达成clear加set。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "sweetness_level",
      "op": "lte",
      "value": 2,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "sweetness_level",
      "op": "lte",
      "value": 2,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000102

原话：风味强度不设具体等级了，改为浓一点优先。

依据：同一字段新条件整体替换旧hard/soft；不把替换表达成clear加set。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [],
  "soft_preferences": [
    {
      "field": "flavor_intensity",
      "preference": "higher",
      "value": null,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [],
  "soft_preferences": [
    {
      "field": "flavor_intensity",
      "preference": "higher",
      "value": null,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "sort": null
}
```

## eval-000103

原话：排序换成价格从高到低。

依据：同一字段新条件整体替换旧hard/soft；不把替换表达成clear加set。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": {
    "field": "price",
    "order": "desc"
  },
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [],
  "soft_preferences": [],
  "sort": {
    "field": "price",
    "order": "desc"
  }
}
```

## eval-000104

原话：全文搜索词改为Dubai Chocolate，原词不要了。

依据：同一字段新条件整体替换旧hard/soft；不把替换表达成clear加set。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": "Dubai Chocolate",
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": "Dubai Chocolate",
  "hard_filters": [],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000105

原话：风味大类改成必须茶与咖啡，原来的水果类不要了。

依据：同一字段新条件整体替换旧hard/soft；不把替换表达成clear加set。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "flavor_family",
      "op": "in",
      "value": null,
      "values": [
        "tea_coffee"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "flavor_family",
      "op": "in",
      "value": null,
      "values": [
        "tea_coffee"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000106

原话：价格不限了，取消预算条件。

依据：明确取消已有条件，仅写clear_fields；不伪造null条件。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [],
  "soft_preferences": [],
  "clear_fields": [
    "price"
  ],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000107

原话：不用限制包装规格了。

依据：明确取消已有条件，仅写clear_fields；不伪造null条件。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [],
  "soft_preferences": [],
  "clear_fields": [
    "size"
  ],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000108

原话：口味不挑了，取消口味要求。

依据：明确取消已有条件，仅写clear_fields；不伪造null条件。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [],
  "soft_preferences": [],
  "clear_fields": [
    "flavor"
  ],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000109

原话：常温偏好撤销，储存条件不限。

依据：明确取消已有条件，仅写clear_fields；不伪造null条件。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [],
  "soft_preferences": [],
  "clear_fields": [
    "storage"
  ],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000110

原话：质构限制取消。

依据：明确取消已有条件，仅写clear_fields；不伪造null条件。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [],
  "soft_preferences": [],
  "clear_fields": [
    "texture"
  ],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000111

原话：排序取消，恢复默认排序。

依据：明确取消已有条件，仅写clear_fields；不伪造null条件。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [],
  "soft_preferences": [],
  "clear_fields": [
    "sort"
  ],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000112

原话：把全文搜索词清掉。

依据：明确取消已有条件，仅写clear_fields；不伪造null条件。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [],
  "soft_preferences": [],
  "clear_fields": [
    "query_text"
  ],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000113

原话：价格和规格这两个条件都取消。

依据：明确取消已有条件，仅写clear_fields；不伪造null条件。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [],
  "soft_preferences": [],
  "clear_fields": [
    "price",
    "size"
  ],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000114

原话：取消甜度条件，硬限制和偏好都不保留。

依据：明确取消已有条件，仅写clear_fields；不伪造null条件。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [],
  "soft_preferences": [],
  "clear_fields": [
    "sweetness_level"
  ],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000115

原话：耐烤不再作为筛选条件。

依据：明确取消已有条件，仅写clear_fields；不伪造null条件。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [],
  "soft_preferences": [],
  "clear_fields": [
    "bake_stable"
  ],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000116

原话：口味换成必须抹茶，20美元预算不变。

依据：只提交修改/新增字段，其他旧字段经合并保留，不回填Patch。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "in",
      "value": null,
      "values": [
        "matcha"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "price",
      "op": "lte",
      "value": 20,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "USD"
    },
    {
      "field": "flavor",
      "op": "in",
      "value": null,
      "values": [
        "matcha"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000117

原话：预算提高到30美元以内，草莓味不变。

依据：只提交修改/新增字段，其他旧字段经合并保留，不回填Patch。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "price",
      "op": "lte",
      "value": 30,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "USD"
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "in",
      "value": null,
      "values": [
        "strawberry"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "price",
      "op": "lte",
      "value": 30,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "USD"
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000118

原话：规格改成1公斤装，冷藏要求保持。

依据：只提交修改/新增字段，其他旧字段经合并保留，不回填Patch。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "size",
      "op": "eq",
      "value": 1,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "kg"
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "storage",
      "op": "in",
      "value": null,
      "values": [
        "refrigerated"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "size",
      "op": "eq",
      "value": 1,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "kg"
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000119

原话：用途改成马卡龙，夹馅方式照旧。

依据：只提交修改/新增字段，其他旧字段经合并保留，不回填Patch。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "application",
      "op": "in",
      "value": null,
      "values": [
        "macaron"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "use_mode",
      "op": "in",
      "value": null,
      "values": [
        "fill"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "application",
      "op": "in",
      "value": null,
      "values": [
        "macaron"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000120

原话：改为淋面使用，奶油酱形态不变。

依据：只提交修改/新增字段，其他旧字段经合并保留，不回填Patch。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "use_mode",
      "op": "in",
      "value": null,
      "values": [
        "drizzle"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "product_type",
      "op": "in",
      "value": null,
      "values": [
        "cream_spread"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "use_mode",
      "op": "in",
      "value": null,
      "values": [
        "drizzle"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000121

原话：质构换成有颗粒，纯素声明要求不变。

依据：只提交修改/新增字段，其他旧字段经合并保留，不回填Patch。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "texture",
      "op": "in",
      "value": null,
      "values": [
        "chunky"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "dietary_claim",
      "op": "in",
      "value": null,
      "values": [
        "vegan"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "texture",
      "op": "in",
      "value": null,
      "values": [
        "chunky"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000122

原话：口味改成必须香草，花生过敏原排除照旧。

依据：只提交修改/新增字段，其他旧字段经合并保留，不回填Patch。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "in",
      "value": null,
      "values": [
        "vanilla"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "allergen",
      "op": "not_in",
      "value": null,
      "values": [
        "peanut"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "flavor",
      "op": "in",
      "value": null,
      "values": [
        "vanilla"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000123

原话：甜度换成最多2级，耐烤要求不动。

依据：只提交修改/新增字段，其他旧字段经合并保留，不回填Patch。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "sweetness_level",
      "op": "lte",
      "value": 2,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "bake_stable",
      "op": "eq",
      "value": true,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "sweetness_level",
      "op": "lte",
      "value": 2,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000124

原话：风味强度改为浓一点优先，抹茶口味不变。

依据：只提交修改/新增字段，其他旧字段经合并保留，不回填Patch。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [],
  "soft_preferences": [
    {
      "field": "flavor_intensity",
      "preference": "higher",
      "value": null,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "in",
      "value": null,
      "values": [
        "matcha"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [
    {
      "field": "flavor_intensity",
      "preference": "higher",
      "value": null,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "sort": null
}
```

## eval-000125

原话：储存改成必须常温，价格排序保持。

依据：只提交修改/新增字段，其他旧字段经合并保留，不回填Patch。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "storage",
      "op": "in",
      "value": null,
      "values": [
        "shelf_stable"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "storage",
      "op": "in",
      "value": null,
      "values": [
        "shelf_stable"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": {
    "field": "price",
    "order": "asc"
  }
}
```

## eval-000126

原话：排序改为评分从高到低，全文词保持。

依据：只提交修改/新增字段，其他旧字段经合并保留，不回填Patch。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": {
    "field": "rating",
    "order": "desc"
  },
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": "Dubai Chocolate",
  "hard_filters": [
    {
      "field": "flavor",
      "op": "in",
      "value": null,
      "values": [
        "dark_chocolate"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": {
    "field": "rating",
    "order": "desc"
  }
}
```

## eval-000127

原话：口味硬条件改成最好开心果，原预算不变。

依据：只提交修改/新增字段，其他旧字段经合并保留，不回填Patch。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [],
  "soft_preferences": [
    {
      "field": "flavor",
      "preference": "prefer",
      "value": null,
      "values": [
        "pistachio"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "price",
      "op": "lte",
      "value": 24,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "USD"
    }
  ],
  "soft_preferences": [
    {
      "field": "flavor",
      "preference": "prefer",
      "value": null,
      "values": [
        "pistachio"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "sort": null
}
```

## eval-000128

原话：只增加必须无蛋的声明要求，原来的草莓味和常温条件都保留。

依据：只提交修改/新增字段，其他旧字段经合并保留，不回填Patch。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "dietary_claim",
      "op": "in",
      "value": null,
      "values": [
        "egg_free"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "in",
      "value": null,
      "values": [
        "strawberry"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "storage",
      "op": "in",
      "value": null,
      "values": [
        "shelf_stable"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    },
    {
      "field": "dietary_claim",
      "op": "in",
      "value": null,
      "values": [
        "egg_free"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000129

原话：预算改成最多28美元，原来最好纯素的偏好不变。

依据：只提交修改/新增字段，其他旧字段经合并保留，不回填Patch。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "price",
      "op": "lte",
      "value": 28,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "USD"
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "price",
      "op": "lte",
      "value": 28,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "USD"
    }
  ],
  "soft_preferences": [
    {
      "field": "dietary_claim",
      "preference": "prefer",
      "value": null,
      "values": [
        "vegan"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "sort": null
}
```

## eval-000130

原话：口味换成必须柠檬，原有规格和排序都不动。

依据：只提交修改/新增字段，其他旧字段经合并保留，不回填Patch。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "in",
      "value": null,
      "values": [
        "lemon"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "size",
      "op": "eq",
      "value": 500,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "g"
    },
    {
      "field": "flavor",
      "op": "in",
      "value": null,
      "values": [
        "lemon"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": {
    "field": "newest",
    "order": "desc"
  }
}
```

## eval-000131

原话：价格必须恰好9美元。

依据：数字与闭区间忠实原话；省略币种时unit=null，不进行货币推断。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "price",
      "op": "eq",
      "value": 9,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "USD"
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "price",
      "op": "eq",
      "value": 9,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "USD"
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000132

原话：价格上限是19美元，含19。

依据：数字与闭区间忠实原话；省略币种时unit=null，不进行货币推断。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "price",
      "op": "lte",
      "value": 19,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "USD"
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "price",
      "op": "lte",
      "value": 19,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "USD"
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000133

原话：只看至少10美元的，含10美元。

依据：数字与闭区间忠实原话；省略币种时unit=null，不进行货币推断。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "price",
      "op": "gte",
      "value": 10,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "USD"
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "price",
      "op": "gte",
      "value": 10,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "USD"
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000134

原话：价格必须在12到26美元之间，包含两端。

依据：数字与闭区间忠实原话；省略币种时unit=null，不进行货币推断。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "price",
      "op": "between",
      "value": null,
      "values": [],
      "min_value": 12,
      "max_value": 26,
      "unit": "USD"
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "price",
      "op": "between",
      "value": null,
      "values": [],
      "min_value": 12,
      "max_value": 26,
      "unit": "USD"
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000135

原话：只看价格为0美元的。

依据：数字与闭区间忠实原话；省略币种时unit=null，不进行货币推断。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "price",
      "op": "eq",
      "value": 0,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "USD"
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "price",
      "op": "eq",
      "value": 0,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "USD"
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000136

原话：标价最多0美元。

依据：数字与闭区间忠实原话；省略币种时unit=null，不进行货币推断。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "price",
      "op": "lte",
      "value": 0,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "USD"
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "price",
      "op": "lte",
      "value": 0,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "USD"
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000137

原话：单件价格必须是12.5美元。

依据：数字与闭区间忠实原话；省略币种时unit=null，不进行货币推断。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "price",
      "op": "eq",
      "value": 12.5,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "USD"
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "price",
      "op": "eq",
      "value": 12.5,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "USD"
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000138

原话：最多19.99美元一件。

依据：数字与闭区间忠实原话；省略币种时unit=null，不进行货币推断。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "price",
      "op": "lte",
      "value": 19.99,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "USD"
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "price",
      "op": "lte",
      "value": 19.99,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "USD"
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000139

原话：单价最低0.5美元。

依据：数字与闭区间忠实原话；省略币种时unit=null，不进行货币推断。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "price",
      "op": "gte",
      "value": 0.5,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "USD"
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "price",
      "op": "gte",
      "value": 0.5,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "USD"
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000140

原话：价格限定8.5至13.5美元，含两端。

依据：数字与闭区间忠实原话；省略币种时unit=null，不进行货币推断。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "price",
      "op": "between",
      "value": null,
      "values": [],
      "min_value": 8.5,
      "max_value": 13.5,
      "unit": "USD"
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "price",
      "op": "between",
      "value": null,
      "values": [],
      "min_value": 8.5,
      "max_value": 13.5,
      "unit": "USD"
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000141

原话：价格最多20，币种暂不指定。

依据：数字与闭区间忠实原话；省略币种时unit=null，不进行货币推断。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "price",
      "op": "lte",
      "value": 20,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "price",
      "op": "lte",
      "value": 20,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000142

原话：单价必须15，先不指定货币。

依据：数字与闭区间忠实原话；省略币种时unit=null，不进行货币推断。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "price",
      "op": "eq",
      "value": 15,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "price",
      "op": "eq",
      "value": 15,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000143

原话：单价至少6，币种没有要求。

依据：数字与闭区间忠实原话；省略币种时unit=null，不进行货币推断。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "price",
      "op": "gte",
      "value": 6,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "price",
      "op": "gte",
      "value": 6,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000144

原话：价格限定11到17，货币不指定。

依据：数字与闭区间忠实原话；省略币种时unit=null，不进行货币推断。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "price",
      "op": "between",
      "value": null,
      "values": [],
      "min_value": 11,
      "max_value": 17,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "price",
      "op": "between",
      "value": null,
      "values": [],
      "min_value": 11,
      "max_value": 17,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000145

原话：价格只能是7到7美元，两个边界相同。

依据：数字与闭区间忠实原话；省略币种时unit=null，不进行货币推断。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "price",
      "op": "between",
      "value": null,
      "values": [],
      "min_value": 7,
      "max_value": 7,
      "unit": "USD"
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "price",
      "op": "between",
      "value": null,
      "values": [],
      "min_value": 7,
      "max_value": 7,
      "unit": "USD"
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000146

原话：包装净含量必须是300克。

依据：提取包装净含量；保留g/kg/oz，不在Gold中换算为克。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "size",
      "op": "eq",
      "value": 300,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "g"
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "size",
      "op": "eq",
      "value": 300,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "g"
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000147

原话：只看至少750克装。

依据：提取包装净含量；保留g/kg/oz，不在Gold中换算为克。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "size",
      "op": "gte",
      "value": 750,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "g"
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "size",
      "op": "gte",
      "value": 750,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "g"
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000148

原话：最多400克一包。

依据：提取包装净含量；保留g/kg/oz，不在Gold中换算为克。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "size",
      "op": "lte",
      "value": 400,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "g"
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "size",
      "op": "lte",
      "value": 400,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "g"
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000149

原话：净含量限定200到600克，含边界。

依据：提取包装净含量；保留g/kg/oz，不在Gold中换算为克。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "size",
      "op": "between",
      "value": null,
      "values": [],
      "min_value": 200,
      "max_value": 600,
      "unit": "g"
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "size",
      "op": "between",
      "value": null,
      "values": [],
      "min_value": 200,
      "max_value": 600,
      "unit": "g"
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000150

原话：必须是2公斤装。

依据：提取包装净含量；保留g/kg/oz，不在Gold中换算为克。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "size",
      "op": "eq",
      "value": 2,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "kg"
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "size",
      "op": "eq",
      "value": 2,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "kg"
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000151

原话：净含量至少0.5公斤。

依据：提取包装净含量；保留g/kg/oz，不在Gold中换算为克。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "size",
      "op": "gte",
      "value": 0.5,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "kg"
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "size",
      "op": "gte",
      "value": 0.5,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "kg"
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000152

原话：每包不超过1.5公斤。

依据：提取包装净含量；保留g/kg/oz，不在Gold中换算为克。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "size",
      "op": "lte",
      "value": 1.5,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "kg"
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "size",
      "op": "lte",
      "value": 1.5,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "kg"
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000153

原话：规格必须在0.25到1公斤之间。

依据：提取包装净含量；保留g/kg/oz，不在Gold中换算为克。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "size",
      "op": "between",
      "value": null,
      "values": [],
      "min_value": 0.25,
      "max_value": 1,
      "unit": "kg"
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "size",
      "op": "between",
      "value": null,
      "values": [],
      "min_value": 0.25,
      "max_value": 1,
      "unit": "kg"
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000154

原话：要恰好8oz的包装。

依据：提取包装净含量；保留g/kg/oz，不在Gold中换算为克。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "size",
      "op": "eq",
      "value": 8,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "oz"
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "size",
      "op": "eq",
      "value": 8,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "oz"
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000155

原话：包装至少12盎司。

依据：提取包装净含量；保留g/kg/oz，不在Gold中换算为克。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "size",
      "op": "gte",
      "value": 12,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "oz"
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "size",
      "op": "gte",
      "value": 12,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "oz"
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000156

原话：甜度希望低一些，不要设等级上限。

依据：相对表达为lower/higher/around软偏好；无锚点不猜数值。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [],
  "soft_preferences": [
    {
      "field": "sweetness_level",
      "preference": "lower",
      "value": null,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [],
  "soft_preferences": [
    {
      "field": "sweetness_level",
      "preference": "lower",
      "value": null,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "sort": null
}
```

## eval-000157

原话：甜度希望高一点，具体等级不限。

依据：相对表达为lower/higher/around软偏好；无锚点不猜数值。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [],
  "soft_preferences": [
    {
      "field": "sweetness_level",
      "preference": "higher",
      "value": null,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [],
  "soft_preferences": [
    {
      "field": "sweetness_level",
      "preference": "higher",
      "value": null,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "sort": null
}
```

## eval-000158

原话：甜度最好在3级左右。

依据：相对表达为lower/higher/around软偏好；无锚点不猜数值。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [],
  "soft_preferences": [
    {
      "field": "sweetness_level",
      "preference": "around",
      "value": 3,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [],
  "soft_preferences": [
    {
      "field": "sweetness_level",
      "preference": "around",
      "value": 3,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "sort": null
}
```

## eval-000159

原话：风味希望淡一点，不要猜等级。

依据：相对表达为lower/higher/around软偏好；无锚点不猜数值。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [],
  "soft_preferences": [
    {
      "field": "flavor_intensity",
      "preference": "lower",
      "value": null,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [],
  "soft_preferences": [
    {
      "field": "flavor_intensity",
      "preference": "lower",
      "value": null,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "sort": null
}
```

## eval-000160

原话：风味浓一些优先，没指定强度等级。

依据：相对表达为lower/higher/around软偏好；无锚点不猜数值。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [],
  "soft_preferences": [
    {
      "field": "flavor_intensity",
      "preference": "higher",
      "value": null,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [],
  "soft_preferences": [
    {
      "field": "flavor_intensity",
      "preference": "higher",
      "value": null,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "sort": null
}
```

## eval-000161

原话：风味强度最好在4级附近。

依据：相对表达为lower/higher/around软偏好；无锚点不猜数值。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [],
  "soft_preferences": [
    {
      "field": "flavor_intensity",
      "preference": "around",
      "value": 4,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [],
  "soft_preferences": [
    {
      "field": "flavor_intensity",
      "preference": "around",
      "value": 4,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "sort": null
}
```

## eval-000162

原话：价格便宜一些就好，不设预算。

依据：相对表达为lower/higher/around软偏好；无锚点不猜数值。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [],
  "soft_preferences": [
    {
      "field": "price",
      "preference": "lower",
      "value": null,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [],
  "soft_preferences": [
    {
      "field": "price",
      "preference": "lower",
      "value": null,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "sort": null
}
```

## eval-000163

原话：价格最好在15美元左右。

依据：相对表达为lower/higher/around软偏好；无锚点不猜数值。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [],
  "soft_preferences": [
    {
      "field": "price",
      "preference": "around",
      "value": 15,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "USD"
    }
  ],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [],
  "soft_preferences": [
    {
      "field": "price",
      "preference": "around",
      "value": 15,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "USD"
    }
  ],
  "sort": null
}
```

## eval-000164

原话：包装希望小一点，没要求具体规格。

依据：相对表达为lower/higher/around软偏好；无锚点不猜数值。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [],
  "soft_preferences": [
    {
      "field": "size",
      "preference": "lower",
      "value": null,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [],
  "soft_preferences": [
    {
      "field": "size",
      "preference": "lower",
      "value": null,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "sort": null
}
```

## eval-000165

原话：净含量最好在1公斤左右。

依据：相对表达为lower/higher/around软偏好；无锚点不猜数值。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [],
  "soft_preferences": [
    {
      "field": "size",
      "preference": "around",
      "value": 1,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "kg"
    }
  ],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [],
  "soft_preferences": [
    {
      "field": "size",
      "preference": "around",
      "value": 1,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "kg"
    }
  ],
  "sort": null
}
```

## eval-000166

原话：请按价格从低到高排列。

依据：只输出明示排序；不虚构过滤条件。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": {
    "field": "price",
    "order": "asc"
  },
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [],
  "soft_preferences": [],
  "sort": {
    "field": "price",
    "order": "asc"
  }
}
```

## eval-000167

原话：按价格由高到低显示。

依据：只输出明示排序；不虚构过滤条件。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": {
    "field": "price",
    "order": "desc"
  },
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [],
  "soft_preferences": [],
  "sort": {
    "field": "price",
    "order": "desc"
  }
}
```

## eval-000168

原话：先显示最新发布的。

依据：只输出明示排序；不虚构过滤条件。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": {
    "field": "newest",
    "order": "desc"
  },
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [],
  "soft_preferences": [],
  "sort": {
    "field": "newest",
    "order": "desc"
  }
}
```

## eval-000169

原话：按热度从高到低排。

依据：只输出明示排序；不虚构过滤条件。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": {
    "field": "popularity",
    "order": "desc"
  },
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [],
  "soft_preferences": [],
  "sort": {
    "field": "popularity",
    "order": "desc"
  }
}
```

## eval-000170

原话：评分最高的排前面。

依据：只输出明示排序；不虚构过滤条件。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": {
    "field": "rating",
    "order": "desc"
  },
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [],
  "soft_preferences": [],
  "sort": {
    "field": "rating",
    "order": "desc"
  }
}
```

## eval-000171

原话：全文搜索关键词用Dubai Chocolate。

依据：用户明示商品全文词；不创造Registry枚举。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": "Dubai Chocolate",
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": "Dubai Chocolate",
  "hard_filters": [],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000172

原话：请用Paris Style作为全文检索词。

依据：用户明示商品全文词；不创造Registry枚举。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": "Paris Style",
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": "Paris Style",
  "hard_filters": [],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000173

原话：在商品全文中搜索限定词Christmas Edition。

依据：用户明示商品全文词；不创造Registry枚举。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": "Christmas Edition",
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": "Christmas Edition",
  "hard_filters": [],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000174

原话：全文检索关键词设为Sakura Collection。

依据：用户明示商品全文词；不创造Registry枚举。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": "Sakura Collection",
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": "Sakura Collection",
  "hard_filters": [],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000175

原话：商品全文关键词只用Summer Special。

依据：用户明示商品全文词；不创造Registry枚举。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": "Summer Special",
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": "Summer Special",
  "hard_filters": [],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000176

原话：必须是开心果味，另外整体高级一点。

依据：抽象评价无法安全映射，保留原文片段；不猜价格排序或过滤条件。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "in",
      "value": null,
      "values": [
        "pistachio"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": [
    "整体高级一点"
  ]
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "in",
      "value": null,
      "values": [
        "pistachio"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000177

原话：必须用于蛋糕，还要有仪式感。

依据：抽象评价无法安全映射，保留原文片段；不猜价格排序或过滤条件。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "application",
      "op": "in",
      "value": null,
      "values": [
        "cake_cupcake"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": [
    "有仪式感"
  ]
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "application",
      "op": "in",
      "value": null,
      "values": [
        "cake_cupcake"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000178

原话：必须是草莓味，另外颜值高一点。

依据：抽象评价无法安全映射，保留原文片段；不猜价格排序或过滤条件。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "in",
      "value": null,
      "values": [
        "strawberry"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": [
    "颜值高一点"
  ]
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "in",
      "value": null,
      "values": [
        "strawberry"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000179

原话：必须常温保存，还要包装有故事感。

依据：抽象评价无法安全映射，保留原文片段；不猜价格排序或过滤条件。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "storage",
      "op": "in",
      "value": null,
      "values": [
        "shelf_stable"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": [
    "包装有故事感"
  ]
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "storage",
      "op": "in",
      "value": null,
      "values": [
        "shelf_stable"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000180

原话：必须有纯素声明，还要小众一点。

依据：抽象评价无法安全映射，保留原文片段；不猜价格排序或过滤条件。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "dietary_claim",
      "op": "in",
      "value": null,
      "values": [
        "vegan"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": [
    "小众一点"
  ]
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "dietary_claim",
      "op": "in",
      "value": null,
      "values": [
        "vegan"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000181

原话：必须是淋酱形态，还要有高级餐厅氛围。

依据：抽象评价无法安全映射，保留原文片段；不猜价格排序或过滤条件。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "product_type",
      "op": "in",
      "value": null,
      "values": [
        "sauce_topping"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": [
    "有高级餐厅氛围"
  ]
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "product_type",
      "op": "in",
      "value": null,
      "values": [
        "sauce_topping"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000182

原话：净含量必须500克，还要品牌有情怀。

依据：抽象评价无法安全映射，保留原文片段；不猜价格排序或过滤条件。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "size",
      "op": "eq",
      "value": 500,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "g"
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": [
    "品牌有情怀"
  ]
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "size",
      "op": "eq",
      "value": 500,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "g"
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000183

原话：价格最多21美元，还要适合拍照出片。

依据：抽象评价无法安全映射，保留原文片段；不猜价格排序或过滤条件。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "price",
      "op": "lte",
      "value": 21,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "USD"
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": [
    "适合拍照出片"
  ]
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "price",
      "op": "lte",
      "value": 21,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "USD"
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000184

原话：必须黑巧克力味，还要名字听起来高级。

依据：抽象评价无法安全映射，保留原文片段；不猜价格排序或过滤条件。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "in",
      "value": null,
      "values": [
        "dark_chocolate"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": [
    "名字听起来高级"
  ]
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "in",
      "value": null,
      "values": [
        "dark_chocolate"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000185

原话：必须冷藏保存，还要整体很有格调。

依据：抽象评价无法安全映射，保留原文片段；不猜价格排序或过滤条件。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": false,
  "hard_filters": [
    {
      "field": "storage",
      "op": "in",
      "value": null,
      "values": [
        "refrigerated"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": [
    "整体很有格调"
  ]
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "storage",
      "op": "in",
      "value": null,
      "values": [
        "refrigerated"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000186

原话：前面的全不要了，重新找必须草莓味的。

依据：reset丢弃全部旧状态后应用新条件；不附带冗余clear_fields。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": true,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "in",
      "value": null,
      "values": [
        "strawberry"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "in",
      "value": null,
      "values": [
        "strawberry"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000187

原话：从头搜索，只要求抹茶味。

依据：reset丢弃全部旧状态后应用新条件；不附带冗余clear_fields。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": true,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "in",
      "value": null,
      "values": [
        "matcha"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "flavor",
      "op": "in",
      "value": null,
      "values": [
        "matcha"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000188

原话：清空所有旧条件，新的预算是最多35美元。

依据：reset丢弃全部旧状态后应用新条件；不附带冗余clear_fields。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": true,
  "hard_filters": [
    {
      "field": "price",
      "op": "lte",
      "value": 35,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "USD"
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "price",
      "op": "lte",
      "value": 35,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "USD"
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000189

原话：重新开始，只要500克装。

依据：reset丢弃全部旧状态后应用新条件；不附带冗余clear_fields。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": true,
  "hard_filters": [
    {
      "field": "size",
      "op": "eq",
      "value": 500,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "g"
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "size",
      "op": "eq",
      "value": 500,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": "g"
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000190

原话：之前的条件都取消，现在必须用于泡芙。

依据：reset丢弃全部旧状态后应用新条件；不附带冗余clear_fields。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": true,
  "hard_filters": [
    {
      "field": "application",
      "op": "in",
      "value": null,
      "values": [
        "choux_puff"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "application",
      "op": "in",
      "value": null,
      "values": [
        "choux_puff"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000191

原话：重置搜索，只选淋面使用方式。

依据：reset丢弃全部旧状态后应用新条件；不附带冗余clear_fields。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": true,
  "hard_filters": [
    {
      "field": "use_mode",
      "op": "in",
      "value": null,
      "values": [
        "drizzle"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "use_mode",
      "op": "in",
      "value": null,
      "values": [
        "drizzle"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000192

原话：全部重新来，质构必须可挤压。

依据：reset丢弃全部旧状态后应用新条件；不附带冗余clear_fields。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": true,
  "hard_filters": [
    {
      "field": "texture",
      "op": "in",
      "value": null,
      "values": [
        "squeezable"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "texture",
      "op": "in",
      "value": null,
      "values": [
        "squeezable"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000193

原话：旧条件全部撤销，只筛未开封冷藏。

依据：reset丢弃全部旧状态后应用新条件；不附带冗余clear_fields。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": true,
  "hard_filters": [
    {
      "field": "storage",
      "op": "in",
      "value": null,
      "values": [
        "refrigerated"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "storage",
      "op": "in",
      "value": null,
      "values": [
        "refrigerated"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000194

原话：清空之前的搜索，只要求商品耐烤。

依据：reset丢弃全部旧状态后应用新条件；不附带冗余clear_fields。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": true,
  "hard_filters": [
    {
      "field": "bake_stable",
      "op": "eq",
      "value": true,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "bake_stable",
      "op": "eq",
      "value": true,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000195

原话：从头找，只要求有无大豆声明。

依据：reset丢弃全部旧状态后应用新条件；不附带冗余clear_fields。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": true,
  "hard_filters": [
    {
      "field": "dietary_claim",
      "op": "in",
      "value": null,
      "values": [
        "soy_free"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "dietary_claim",
      "op": "in",
      "value": null,
      "values": [
        "soy_free"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000196

原话：全部重置，现在只排除芝麻过敏原。

依据：reset丢弃全部旧状态后应用新条件；不附带冗余clear_fields。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": true,
  "hard_filters": [
    {
      "field": "allergen",
      "op": "not_in",
      "value": null,
      "values": [
        "sesame"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "allergen",
      "op": "not_in",
      "value": null,
      "values": [
        "sesame"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000197

原话：重开一次搜索，只要水果风味大类。

依据：reset丢弃全部旧状态后应用新条件；不附带冗余clear_fields。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": true,
  "hard_filters": [
    {
      "field": "flavor_family",
      "op": "in",
      "value": null,
      "values": [
        "fruit"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [
    {
      "field": "flavor_family",
      "op": "in",
      "value": null,
      "values": [
        "fruit"
      ],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "soft_preferences": [],
  "sort": null
}
```

## eval-000198

原话：旧搜索不要了，新的只希望甜度低一些。

依据：reset丢弃全部旧状态后应用新条件；不附带冗余clear_fields。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": true,
  "hard_filters": [],
  "soft_preferences": [
    {
      "field": "sweetness_level",
      "preference": "lower",
      "value": null,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [],
  "soft_preferences": [
    {
      "field": "sweetness_level",
      "preference": "lower",
      "value": null,
      "values": [],
      "min_value": null,
      "max_value": null,
      "unit": null
    }
  ],
  "sort": null
}
```

## eval-000199

原话：所有旧条件清空，新搜索只按最新发布排序。

依据：reset丢弃全部旧状态后应用新条件；不附带冗余clear_fields。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": true,
  "hard_filters": [],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": {
    "field": "newest",
    "order": "desc"
  },
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [],
  "soft_preferences": [],
  "sort": {
    "field": "newest",
    "order": "desc"
  }
}
```

## eval-000200

原话：把前面的条件全部清空，暂时不添加新条件。

依据：reset丢弃全部旧状态后应用新条件；不附带冗余clear_fields。

本轮Gold：

```json
{
  "schema_version": "1.0",
  "reset": true,
  "hard_filters": [],
  "soft_preferences": [],
  "clear_fields": [],
  "query_text": null,
  "sort": null,
  "unmapped_terms": []
}
```

Gold合并状态：

```json
{
  "query_text": null,
  "hard_filters": [],
  "soft_preferences": [],
  "sort": null
}
```

