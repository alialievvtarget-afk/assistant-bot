// KP Plugin — каркас для генерации редактируемых слайдов в Figma
// ВАЖНО: см. INSTRUCTION.md рядом — правила Figma sandbox (без spread-оператора и т.д.)

const W = 1920, H = 1080;
const GAP = 100; // отступ между слайдами по X

// Дефолтная палитра — замени под клиента, если нужно
const C = {
  bg:        {r:0.922, g:0.922, b:0.922},
  blue:      {r:0.290, g:0.565, b:0.851},
  blueDark:  {r:0.169, g:0.369, b:0.655},
  white:     {r:1,     g:1,     b:1    },
  dark:      {r:0.102, g:0.102, b:0.102},
  gray:      {r:0.4,   g:0.4,   b:0.4  },
  lightGray: {r:0.6,   g:0.6,   b:0.6  },
};

const FONT_FAMILY = 'Inter'; // смени на 'Montserrat' если шрифт есть у пользователя в Figma

const solid = c => [{type:'SOLID', color:c}];
const gradFill = (c1, c2) => [{
  type:'GRADIENT_LINEAR',
  gradientTransform:[[1,0,0],[0,1,0]],
  gradientStops:[
    {position:0, color:{r:c1.r, g:c1.g, b:c1.b, a:1}},
    {position:1, color:{r:c2.r, g:c2.g, b:c2.b, a:1}}
  ]
}];

function mkFrame(parent, x, y, w, h, fill, radius, name) {
  const f = figma.createFrame();
  f.name = name || 'frame';
  f.resize(w, h);
  f.x = x; f.y = y;
  f.fills = fill || solid(C.white);
  f.cornerRadius = radius || 0;
  f.clipsContent = true;
  parent.appendChild(f);
  return f;
}

function mkRect(parent, x, y, w, h, fill, radius) {
  const r = figma.createRectangle();
  r.resize(w, h);
  r.x = x; r.y = y;
  r.fills = fill;
  r.cornerRadius = radius || 0;
  parent.appendChild(r);
  return r;
}

async function mkText(parent, txt, x, y, w, size, style, color, align, lh, ls) {
  await figma.loadFontAsync({family: FONT_FAMILY, style: style || 'Regular'});
  const t = figma.createText();
  t.fontName = {family: FONT_FAMILY, style: style || 'Regular'};
  t.fontSize = size;
  t.fills = solid(color || C.dark);
  t.textAlignHorizontal = align || 'LEFT';
  if (lh) t.lineHeight = {value: lh, unit: 'PIXELS'};
  if (ls) t.letterSpacing = {value: ls, unit: 'PIXELS'};
  t.x = x; t.y = y;
  if (w) { t.textAutoResize = 'HEIGHT'; t.resize(w, 50); }
  else   { t.textAutoResize = 'WIDTH_AND_HEIGHT'; }
  t.characters = txt;
  parent.appendChild(t);
  return t;
}

// ==== Пример: один слайд-заголовок (замени/расширь под реальный контент) ====
async function buildSlide1(page, index) {
  const x = index * (W + GAP);
  const slide = mkFrame(page, x, 0, W, H, solid(C.bg), 0, `Slide ${index + 1}`);

  // пример карточки
  mkRect(slide, 120, 120, W - 240, H - 240, solid(C.white), 24);

  await mkText(slide, 'Заголовок слайда', 160, 160, W - 320, 56, 'Bold', C.dark);
  await mkText(slide, 'Подзаголовок или тезис', 160, 240, W - 320, 28, 'Regular', C.gray);

  return slide;
}

// ==== Точка входа ====
async function main() {
  const page = figma.currentPage;

  // TODO: заменить на реальный список слайдов из контента пользователя
  const slides = [buildSlide1];

  const built = [];
  for (let i = 0; i < slides.length; i++) {
    built.push(await slides[i](page, i));
  }

  figma.viewport.scrollAndZoomIntoView(built);
  figma.closePlugin();
}

main().catch(e => {
  figma.notify('Ошибка: ' + e.message);
  figma.closePlugin();
});
