import os

if not os.path.exists("images_rename"):
    os.mkdir("images_rename")

images_list = os.listdir('images/')
images_list.sort()
for i in range(len(images_list)):
    if len(str(i)) == 1:
        command = 'cp images/"' + images_list[i] + '" ./images_rename/' + '000' + str(i) + '.png'
    elif len(str(i)) == 2:
        command = 'cp images/"' + images_list[i] + '" ./images_rename/' + '00' + str(i) + '.png'
    elif len(str(i)) == 3:
        command = 'cp images/"' + images_list[i] + '" ./images_rename/' + '0' + str(i) + '.png'
    else:
        command = 'cp images/"' + images_list[i] + '" ./images_rename/' + str(i) + '.png'
    print(command)
    os.system(command)